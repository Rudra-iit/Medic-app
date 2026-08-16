import { Injectable, signal } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { tap } from 'rxjs/operators';
import { Observable } from 'rxjs';
import { environment } from '../../environments/environment';

export interface AuthUser {
  id: number;
  email: string;
  role: string;
  created_at: string;
}

export interface RoleRequestStatus {
  id: number;
  email: string;
  role: string;
  admin_requested: boolean;
  staff_requested: boolean;
  created_at: string;
}

export interface RegisterPayload {
  email: string;
  password: string;
  request_admin?: boolean;
  request_staff?: boolean;
}

export interface LoginPayload {
  email: string;
  password: string;
}

export interface TokenResponse {
  access_token: string;
  token_type: 'bearer';
}

@Injectable({ providedIn: 'root' })
export class AuthService {
  user = signal<AuthUser | null>(null);
  token = signal<string | null>(localStorage.getItem('auth_token'));
  pendingAdminRequests = signal(0);
  pendingStaffRequests = signal(0);

  constructor(private http: HttpClient) {}

  get isAuthenticated(): boolean {
    return !!this.token();
  }

  get isAdmin(): boolean {
    return this.user()?.role === 'admin';
  }

  get isStaff(): boolean {
    return this.user()?.role === 'staff';
  }

  get hasPendingRequests(): boolean {
    return this.pendingAdminRequests() + this.pendingStaffRequests() > 0;
  }

  get pendingRequestCount(): number {
    return this.pendingAdminRequests() + this.pendingStaffRequests();
  }

  private saveToken(token: string): void {
    localStorage.setItem('auth_token', token);
    this.token.set(token);
  }

  private clearAuth(): void {
    localStorage.removeItem('auth_token');
    this.token.set(null);
    this.user.set(null);
  }

  register(payload: RegisterPayload): Observable<TokenResponse> {
    return this.http.post<TokenResponse>(`${environment.apiUrl}/auth/register`, payload).pipe(
      tap((result) => {
        this.saveToken(result.access_token);
        this.loadCurrentUser().subscribe();
      })
    );
  }

  login(payload: LoginPayload): Observable<TokenResponse> {
    return this.http.post<TokenResponse>(`${environment.apiUrl}/auth/login`, payload).pipe(
      tap((result) => {
        this.saveToken(result.access_token);
        this.loadCurrentUser().subscribe();
      })
    );
  }

  logout(): void {
    this.clearAuth();
  }

  loadCurrentUser() {
    return this.http.get<AuthUser>(`${environment.apiUrl}/auth/me`).pipe(
      tap((user) => {
        const normalizedRole = user.role?.trim().toLowerCase() ?? 'client';
        this.user.set({ ...user, role: normalizedRole });
        if (normalizedRole === 'admin') {
          this.refreshAllPendingRequests().subscribe();
        } else {
          this.pendingAdminRequests.set(0);
          this.pendingStaffRequests.set(0);
        }
      })
    );
  }

  refreshAllPendingRequests() {
    return this.refreshPendingRequests('admin').pipe(
      tap(() => this.refreshPendingRequests('staff').subscribe())
    );
  }

  refreshPendingRequests(requestType: 'admin' | 'staff') {
    return this.http
      .get<RoleRequestStatus[]>(`${environment.apiUrl}/admin/user-requests?request_type=${requestType}`)
      .pipe(
        tap((requests) => {
          if (requestType === 'admin') {
            this.pendingAdminRequests.set(requests.length);
          } else {
            this.pendingStaffRequests.set(requests.length);
          }
        })
      );
  }

  getPendingRequests(requestType?: 'admin' | 'staff') {
    const url = `${environment.apiUrl}/admin/user-requests${requestType ? `?request_type=${requestType}` : ''}`;
    return this.http.get<RoleRequestStatus[]>(url);
  }

  respondRoleRequest(
    userId: number,
    requestType: 'admin' | 'staff',
    action: 'approve' | 'deny'
  ) {
    return this.http.patch<RoleRequestStatus>(
      `${environment.apiUrl}/admin/users/${userId}/role-request`,
      {
        request_type: requestType,
        action,
      }
    );
  }

  loadRoleRequestStatus() {
    return this.http.get<RoleRequestStatus>(`${environment.apiUrl}/auth/role-request-status`);
  }
}
