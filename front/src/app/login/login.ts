import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router } from '@angular/router';
import { AuthService, LoginPayload } from '../services/auth.service';

@Component({
  selector: 'app-login',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './login.html',
  styleUrl: './login.css',
})
export class Login {
  email = '';
  password = '';
  loading = false;
  error = '';

  constructor(private authService: AuthService, private router: Router) {}

  submit(): void {
    this.loading = true;
    this.error = '';

    const payload: LoginPayload = {
      email: this.email.trim().toLowerCase(),
      password: this.password,
    };

    this.authService.login(payload).subscribe({
      next: () => {
        this.loading = false;
        this.router.navigate(['/products']);
      },
      error: (err) => {
        this.loading = false;
        this.error = err?.error?.detail ?? 'Login failed. Please check your credentials.';
      },
    });
  }
}
