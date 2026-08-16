// names.service.ts
import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../environments/environment';

const API_URL = environment.apiUrl; // your deployed backend

export interface RegisteredName {
  id: number;
  name: string;
  created_at: string;
}

@Injectable({ providedIn: 'root' })
export class NamesService {
  constructor(private http: HttpClient) {}

  getNames(): Observable<any[]> {
    return this.http.get<any[]>(`${API_URL}/names`);
  }

  addName(name: string): Observable<any> {
    return this.http.post(`${API_URL}/names`, { name });
  }

  deleteName(id: number): Observable<any> {
    return this.http.delete(`${API_URL}/names/${id}`);
  }
}