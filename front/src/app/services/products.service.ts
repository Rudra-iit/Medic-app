import { Injectable } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../environments/environment';

export interface Product {
  id: number;
  name: string;
  category_id: number;
  sku: string;
  dosage_form: string | null;
  strength: string | null;
  unit: string | null;
  quantity_in_stock: number;
  reorder_threshold: number | null;
  expiry_date: string | null; // ISO date string, e.g. "2026-12-31"
  requires_prescription: boolean;
  manufacturer: string | null;
  notes: string | null;
  created_at: string;
  updated_at: string;
}

export interface ProductCreate {
  name: string;
  category_id: number;
  sku: string;
  dosage_form?: string | null;
  strength?: string | null;
  unit?: string | null;
  quantity_in_stock?: number;
  reorder_threshold?: number | null;
  expiry_date?: string | null;
  requires_prescription?: boolean;
  manufacturer?: string | null;
  notes?: string | null;
}

export type ProductUpdate = Partial<ProductCreate>;

@Injectable({ providedIn: 'root' })
export class ProductsService {
  private apiUrl = environment.apiUrl;

  constructor(private http: HttpClient) {}

  /** Pass a categoryId to filter server-side; omit to get all products. */
  getProducts(categoryId?: number | null): Observable<Product[]> {
    let params = new HttpParams();
    if (categoryId != null) {
      params = params.set('category_id', categoryId);
    }
    return this.http.get<Product[]>(`${this.apiUrl}/products`, { params });
  }

  addProduct(product: ProductCreate): Observable<Product> {
    return this.http.post<Product>(`${this.apiUrl}/products`, product);
  }

  updateProduct(id: number, changes: ProductUpdate): Observable<Product> {
    return this.http.patch<Product>(`${this.apiUrl}/products/${id}`, changes);
  }

  deleteProduct(id: number): Observable<void> {
    return this.http.delete<void>(`${this.apiUrl}/products/${id}`);
  }
}
