import { ChangeDetectorRef, Component, NgZone, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router } from '@angular/router';
import { ProductsService, Product, ProductCreate } from '../services/products.service';
import { CategoriesService, Category } from '../services/categories.service';
import { AuthService } from '../services/auth.service';

@Component({
  selector: 'app-products',
  standalone: true,
  imports: [FormsModule, CommonModule],
  templateUrl: './products.html',
  styleUrl: './products.css',
})
export class Products implements OnInit {
  products: Product[] = [];
  categories: Category[] = [];

  selectedCategoryId: number | null = null; // null = "All categories"

  loading = false;
  error = '';

  // New category form
  newCategoryName = '';

  // New product form
  newProduct: ProductCreate = this.emptyProduct();

  constructor(
    private productsService: ProductsService,
    private categoriesService: CategoriesService,
    public authService: AuthService,
    private router: Router,
    private ngZone: NgZone,
    private cdr: ChangeDetectorRef,
  ) {}

  ngOnInit(): void {
    // Allow anonymous users to view products; admin-only actions are controlled
    // in the template via `authService.isAdmin`.
    this.loadCategories();
    this.loadProducts();
  }

  private emptyProduct(): ProductCreate {
    return {
      name: '',
      category_id: 0,
      sku: '',
      dosage_form: '',
      strength: '',
      unit: '',
      quantity_in_stock: 0,
      reorder_threshold: undefined,
      expiry_date: '',
      requires_prescription: false,
      manufacturer: '',
      notes: ''
    };
  }

  loadCategories(): void {
    this.categoriesService.getCategories().subscribe(categories => {
      this.categories = categories;
      
      error: () => {
        this.error = 'Please log in to view products.';
        this.loading = false;
        this.cdr.detectChanges();
      }
    });
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

  onCategoryFilterChange(): void {
    this.loadProducts();
  }

  categoryName(categoryId: number): string {
    return this.categories.find((c) => c.id === categoryId)?.name ?? 'Unknown';
  }

  isLowStock(product: Product): boolean {
    return (
      product.reorder_threshold != null &&
      product.quantity_in_stock <= product.reorder_threshold
    );
  }

  addCategory(): void {
    const trimmed = this.newCategoryName.trim();
    if (!trimmed) return;

    this.categoriesService.addCategory({ name: trimmed }).subscribe({
      next: () => {
        this.newCategoryName = '';
        this.loadCategories();
      },
      error: () => (this.error = 'Failed to add category (maybe it already exists?).')
    });
  }

  addProduct(): void {
    if (!this.newProduct.name.trim() || !this.newProduct.category_id || !this.newProduct.sku.trim()) {
      this.error = 'Name, category, and SKU are required.';
      return;
    }

    // Send empty strings as null so optional fields don't get stored as ""
    const payload: ProductCreate = {
      ...this.newProduct,
      dosage_form: this.newProduct.dosage_form || null,
      strength: this.newProduct.strength || null,
      unit: this.newProduct.unit || null,
      expiry_date: this.newProduct.expiry_date || null,
      manufacturer: this.newProduct.manufacturer || null,
      notes: this.newProduct.notes || null,
      reorder_threshold: this.newProduct.reorder_threshold ?? null
    };

    this.productsService.addProduct(payload).subscribe({
      next: () => {
        this.newProduct = this.emptyProduct();
        this.loadProducts();
      },
      error: (err) => {
        this.error = err?.error?.detail ?? 'Failed to add product.';
      }
    });
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
