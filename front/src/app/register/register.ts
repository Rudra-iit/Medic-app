import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router } from '@angular/router';
import { AuthService, RegisterPayload } from '../services/auth.service';

@Component({
  selector: 'app-register',
  standalone: true,
  imports: [FormsModule, CommonModule],
  templateUrl: './register.html',
  styleUrl: './register.css',
})
export class Register {
  email = '';
  password = '';
  requestAdmin = false;
  requestStaff = false;
  loading = false;
  error = '';

  constructor(private authService: AuthService, private router: Router) {}

  submit(): void {
    this.loading = true;
    this.error = '';

    const payload: RegisterPayload = {
      email: this.email.trim().toLowerCase(),
      password: this.password,
      request_admin: this.requestAdmin,
      request_staff: this.requestStaff,
    };

    this.authService.register(payload).subscribe({
      next: () => {
        this.loading = false;
        this.router.navigate(['/products']);
      },
      error: (err) => {
        this.loading = false;
        this.error = err?.error?.detail ?? 'Registration failed. Please try again.';
      },
    });
  }
}
