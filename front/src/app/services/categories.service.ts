import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../environments/environment';

export interface Category {
  id: number;
  name: string;
  description: string | null;
}

export interface CategoryCreate {
  name: string;
  description?: string | null;
}

@Injectable({ providedIn: 'root' })
export class CategoriesService {
  private apiUrl = environment.apiUrl;

  constructor(private http: HttpClient) {}

  getCategories(): Observable<Category[]> {
    return this.http.get<Category[]>(`${this.apiUrl}/categories`);
  }

  addCategory(category: CategoryCreate): Observable<Category> {
    return this.http.post<Category>(`${this.apiUrl}/categories`, category);
  }

  deleteCategory(id: number): Observable<void> {
    return this.http.delete<void>(`${this.apiUrl}/categories/${id}`);
  }
}