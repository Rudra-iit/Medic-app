import { ChangeDetectorRef, Component, NgZone, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router } from '@angular/router';
import { ProductsService, Product, ProductCreate } from '../services/products.service';
import { CategoriesService, Category } from '../services/categories.service';
import { AuthService } from '../services/auth.service';

@Component({
  selector: 'app-update',
  standalone: true,
  imports: [FormsModule, CommonModule],
  templateUrl: './update.html',
  styleUrl: './update.css',
})
export class Update implements OnInit {
  products: Product[] = [];
  categories: Category[] = [];

  selectedCategoryId: number | null = null; // null = "All categories"

  loading = false;
  error = '';

  constructor(
    private productsService: ProductsService,
    private categoriesService: CategoriesService,
    public authService: AuthService,
    private router: Router,
    private ngZone: NgZone,
    private cdr: ChangeDetectorRef,
  ) {}

  ngOnInit(): void {
    this.loadProducts();
  }

  loadProducts(): void {
  this.loading = true;
  this.productsService.getProducts(this.selectedCategoryId).subscribe({
    next: (data) => {
      this.products = data;
      this.loading = false;
      this.cdr.detectChanges();
    },
    error: () => {
      this.error = 'Please log in to view products.';
      this.loading = false;
      this.cdr.detectChanges();
    }
  });
  }

  isLowStock(product: Product): boolean {
    return (
      product.reorder_threshold != null &&
      product.quantity_in_stock <= product.reorder_threshold
    );
  }
  
  adjustStock(product: Product, delta: number): void {
    const newQty = product.quantity_in_stock + delta;
    if (newQty < 0) return;

    this.productsService.updateProduct(product.id, { quantity_in_stock: newQty }).subscribe({
      next: () => this.loadProducts(),
      error: () => (this.error = 'Failed to update stock.')
    });
  }

  deleteProduct(product: Product): void {
    this.productsService.deleteProduct(product.id).subscribe({
      next: () => this.loadProducts(),
      error: () => (this.error = 'Failed to delete product.')
    });
  }
}
