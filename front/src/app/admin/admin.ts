import { Component, OnInit, effect } from '@angular/core';
import { CommonModule } from '@angular/common';
import { AuthService, RoleRequestStatus } from '../services/auth.service';

@Component({
  selector: 'app-admin',
  imports: [CommonModule],
  templateUrl: './admin.html',
  styleUrl: './admin.css',
})
export class Admin implements OnInit {
  requests: RoleRequestStatus[] = [];
  loading = false;
  error = '';
  currentFilter: 'all' | 'admin' | 'staff' = 'all';

  constructor(public authService: AuthService) {}

  ngOnInit(): void {
    effect(() => {
      if (this.authService.isAdmin) {
        this.loadRequests();
      }
    });
  }

  loadRequests(): void {
    this.loading = true;
    this.error = '';
    const type = this.currentFilter === 'all' ? undefined : this.currentFilter;

    this.authService.getPendingRequests(type).subscribe({
      next: (requests) => {
        this.requests = requests;
        this.loading = false;
      },
      error: (err) => {
        this.error = err?.error?.detail ?? 'Unable to load requests.';
        this.loading = false;
      },
    });
  }

  setFilter(filter: 'all' | 'admin' | 'staff'): void {
    this.currentFilter = filter;
    this.loadRequests();
  }

  respond(user: RoleRequestStatus, action: 'approve' | 'deny'): void {
    this.loading = true;
    this.error = '';
    const requestType = user.admin_requested ? 'admin' : 'staff';

    this.authService.respondRoleRequest(user.id, requestType, action).subscribe({
      next: () => {
        this.authService.refreshAllPendingRequests().subscribe();
        this.loadRequests();
      },
      error: (err) => {
        this.error = err?.error?.detail ?? 'Unable to update request.';
        this.loading = false;
      },
    });
  }
}
