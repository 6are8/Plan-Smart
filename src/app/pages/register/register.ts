import { ChangeDetectorRef, Component } from '@angular/core';
import { Router, RouterLink } from '@angular/router';
import { FormBuilder, FormGroup, ReactiveFormsModule, Validators } from '@angular/forms';
import { HttpClient } from '@angular/common/http';

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

  registerForm: FormGroup;
  backendError: string | null = null;
  successMessage: string | null = null;

  constructor(
    private fb: FormBuilder,
    private http: HttpClient,
    private router: Router,
    private cdr: ChangeDetectorRef
  ) {
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

  submit() {
    if (this.registerForm.invalid) return;

    this.backendError = null;
    this.successMessage = null;

    this.http.post('http://localhost:5000/auth/register', this.registerForm.value)
      .subscribe({
        next: () => {
          this.successMessage = 'Registration successful! Redirecting to login...';
          this.cdr.detectChanges();

          setTimeout(() => {
            this.router.navigate(['/login']);
          }, 5000);
        },
        error: (err) => {
          this.backendError = err.error?.message || 'Registration failed';
          this.cdr.detectChanges();
        }
      });
  }
}
