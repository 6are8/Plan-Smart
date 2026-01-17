import { Injectable } from '@angular/core';
import {
  HttpEvent,
  HttpHandler,
  HttpInterceptor,
  HttpRequest,
  HttpErrorResponse
} from '@angular/common/http';
import { Observable, throwError } from 'rxjs';
import { catchError } from 'rxjs/operators';
import { Router } from '@angular/router';

/**
 * Authentication HTTP interceptor.
 *
 * Responsibilities:
 * - Automatically attaches JWT access token to outgoing HTTP requests
 * - Skips authentication endpoints (/auth/*)
 * - Handles unauthorized (401) responses globally
 * - Logs the user out and redirects to /login if the token is invalid or expired
 */
@Injectable()
export class AuthInterceptor implements HttpInterceptor {

  constructor(private router: Router) {}

  intercept(
    req: HttpRequest<any>,
    next: HttpHandler
  ): Observable<HttpEvent<any>> {

    // Do not attach token to auth endpoints
    if (this.isAuthEndpoint(req.url)) {
      return next.handle(req);
    }

    const token = localStorage.getItem('token');

    // If no token exists, continue without Authorization header
    const requestWithAuth = token ? this.attachToken(req, token) : req;

    return next.handle(requestWithAuth).pipe(
      catchError((error: HttpErrorResponse) => this.handleAuthError(error))
    );
  }

  private isAuthEndpoint(url: string): boolean {
    // Covers /auth/login, /auth/register, /auth/refresh, /auth/logout, etc.
    return url.includes('/auth/');
  }

  private attachToken(request: HttpRequest<any>, token: string): HttpRequest<any> {
    return request.clone({
      setHeaders: {
        Authorization: `Bearer ${token}`
      }
    });
  }

  private handleAuthError(error: HttpErrorResponse) {
    if (error.status === 401) {
      localStorage.removeItem('token');
      localStorage.removeItem('refresh_token');
      this.router.navigate(['/login']);
    }

    return throwError(() => error);
  }
}
