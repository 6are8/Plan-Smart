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
 * - Skips authentication endpoints (login / register)
 * - Handles unauthorized (401) responses globally
 * - Logs the user out and redirects to /login if the token is invalid or expired
 */
@Injectable()
export class AuthInterceptor implements HttpInterceptor {

  constructor(private router: Router) {}

  /**
   * Intercepts outgoing HTTP requests.
   *
   * @param req Original HTTP request
   * @param next HTTP handler
   * @returns Observable of HTTP events
   */
  intercept(
    req: HttpRequest<any>,
    next: HttpHandler
  ): Observable<HttpEvent<any>> {

    if (this.isAuthEndpoint(req.url)) {
      return next.handle(req);
    }

    const token = localStorage.getItem('token');
    const requestWithAuth = token ? this.attachToken(req, token) : req;

    return next.handle(requestWithAuth).pipe(
      catchError((error: HttpErrorResponse) => this.handleAuthError(error))
    );
  }

  /**
   * Determines whether the request URL belongs to authentication endpoints.
   *
   * @param url Request URL
   * @returns True if endpoint should not receive Authorization header
   */
  private isAuthEndpoint(url: string): boolean {
    return url.includes('/auth/login') || url.includes('/auth/register');
  }

  /**
   * Clones the HTTP request and attaches the Authorization header.
   *
   * @param request Original HTTP request
   * @param token JWT access token
   * @returns Cloned HTTP request with Authorization header
   */
  private attachToken(
    request: HttpRequest<any>,
    token: string
  ): HttpRequest<any> {
    return request.clone({
      setHeaders: {
        Authorization: `Bearer ${token}`
      }
    });
  }

  /**
   * Handles authentication-related HTTP errors.
   *
   * If a 401 Unauthorized error is received:
   * - Clears authentication data
   * - Redirects the user to the login page
   *
   * @param error HTTP error response
   * @returns Observable that throws the error
   */
  private handleAuthError(error: HttpErrorResponse) {
    if (error.status === 401) {
      localStorage.removeItem('token');
      localStorage.removeItem('refresh_token');
      this.router.navigate(['/login']);
    }

    return throwError(() => error);
  }
}
