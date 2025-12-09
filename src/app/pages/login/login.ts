import {ChangeDetectorRef, Component} from '@angular/core';
import { Router, RouterLink } from '@angular/router';
import { FormBuilder, FormGroup, ReactiveFormsModule, Validators } from '@angular/forms';
import { HttpClient } from '@angular/common/http';

@Component({
  selector: 'app-login',
  imports: [
    RouterLink,
    ReactiveFormsModule
  ],
  templateUrl: './login.html',
  styleUrl: './login.css',
})
export class Login {
  loginForm: FormGroup;
  backendError: string | null = null;

  constructor(
    private fb: FormBuilder,
    private http: HttpClient,
    private router: Router,
    private cdr: ChangeDetectorRef
  ) {
    this.loginForm = this.fb.group({
      username: ['', [Validators.required, Validators.minLength(3)]],
      password: ['', [Validators.required, Validators.minLength(1)]]
    });
  }

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

          if (res.token) {
            localStorage.setItem('token', res.token);
          }

          // ✅ редирект после успешного входа
          this.router.navigate(['/today']);
        },
        error: (err) => {
          this.backendError = err.error?.message || 'Wrong username or password';
          this.cdr.detectChanges();
        }
      });
  }
}
