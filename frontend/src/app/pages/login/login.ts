import { ChangeDetectorRef, Component } from '@angular/core';
import { Router, RouterLink } from '@angular/router';
import { FormBuilder, FormGroup, ReactiveFormsModule, Validators } from '@angular/forms';
import { HttpClient } from '@angular/common/http';

/**
 * Login page component.
 *
 * Handles:
 * - User authentication
 * - Form validation
 * - JWT token storage
 * - Redirect after successful login
 */
@Component({
  selector: 'app-login',
  standalone: true,
  imports: [
    RouterLink,
    ReactiveFormsModule
  ],
  templateUrl: './login.html',
  styleUrl: './login.css',
})
export class Login {

  /** Reactive form for login inputs */
  loginForm: FormGroup;

  /** Error message returned from backend (if any) */
  backendError: string | null = null;

  constructor(
    private fb: FormBuilder,
    private http: HttpClient,
    private router: Router,
    private cdr: ChangeDetectorRef
  ) {
    /**
     * Initialize login form with validation rules.
     */
    this.loginForm = this.fb.group({
      username: ['', [Validators.required, Validators.minLength(3)]],
      password: ['', [Validators.required, Validators.minLength(1)]]
    });
  }

  /**
   * Submits login form to the backend.
   *
   * Flow:
   * 1. Validate form
   * 2. Send credentials to /auth/login
   * 3. Store JWT tokens
   * 4. Redirect to Today page
   */
  submit() {
    if (this.loginForm.invalid) {
      this.loginForm.markAllAsTouched();
      return;
    }

    this.backendError = null;

    this.http.post<any>('http://localhost:5000/auth/login', this.loginForm.value)
      .subscribe({
        next: (res) => {
          console.log('LOGIN SUCCESS:', res);

          /**
           * Store tokens in localStorage.
           * Access token is used for API calls.
           * Refresh token is reserved for future token refresh.
           */
          if (res.access_token) {
            localStorage.setItem('token', res.access_token);
            localStorage.setItem('refresh_token', res.refresh_token);
          }

          /**
           * Redirect user to Today page after successful login.
           */
          this.router.navigate(['/today']);
        },
        error: (err) => {
          /**
           * Display backend error message if login fails.
           */
          this.backendError = err.error?.message || 'Wrong username or password';
          this.cdr.detectChanges();
        }
      });
  }
}
