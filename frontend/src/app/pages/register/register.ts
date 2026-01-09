import { ChangeDetectorRef, Component } from '@angular/core';
import { Router, RouterLink } from '@angular/router';
import { FormBuilder, FormGroup, ReactiveFormsModule, Validators } from '@angular/forms';
import { HttpClient } from '@angular/common/http';

/**
 * Register page component.
 *
 * Handles:
 * - User registration
 * - Form validation
 * - City selection
 * - Redirect to login after successful registration
 */
@Component({
  selector: 'app-register',
  standalone: true,
  imports: [
    RouterLink,
    ReactiveFormsModule
  ],
  templateUrl: './register.html',
  styleUrl: './register.css',
})
export class Register {

  /** Reactive form for user registration */
  registerForm: FormGroup;

  /** Error message returned from backend (if registration fails) */
  backendError: string | null = null;

  /** Success message displayed after successful registration */
  successMessage: string | null = null;

  constructor(
    private fb: FormBuilder,
    private http: HttpClient,
    private router: Router,
    private cdr: ChangeDetectorRef
  ) {
    /**
     * Initialize registration form with validation rules.
     *
     * Password rules:
     * - Minimum 8 characters
     * - At least one uppercase letter
     * - At least one digit
     */
    this.registerForm = this.fb.group({
      username: ['', [Validators.required, Validators.minLength(3)]],
      password: ['', [
        Validators.required,
        Validators.minLength(8),
        Validators.pattern(/^(?=.*[A-Z])(?=.*\d).+$/)
      ]],
      city: ['', Validators.required]
    });
  }

  /**
   * Submits registration form to the backend.
   *
   * Flow:
   * 1. Validate form
   * 2. Send registration data to /auth/register
   * 3. Show success message
   * 4. Redirect to login page after delay
   */
  submit() {
    if (this.registerForm.invalid) return;

    this.backendError = null;
    this.successMessage = null;

    this.http.post('http://localhost:5000/auth/register', this.registerForm.value)
      .subscribe({
        next: () => {
          /**
           * Display success message after successful registration.
           */
          this.successMessage = 'Registration successful! Redirecting to login...';
          this.cdr.detectChanges();

          /**
           * Redirect user to login page after short delay.
           */
          setTimeout(() => {
            this.router.navigate(['/login']);
          }, 5000);
        },
        error: (err) => {
          /**
           * Display backend error message if registration fails.
           */
          this.backendError = err.error?.error || 'Registration failed';
          this.cdr.detectChanges();
        }
      });
  }
}
