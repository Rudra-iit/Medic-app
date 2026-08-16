import { Routes } from '@angular/router';
import { Register } from './register/register';
import { Products } from './products/products';
import { Dashboard } from './dashboard/dashboard';
import { Login } from './login/login';
import { Admin } from './admin/admin';
import { User } from './user/user';
import { Cart } from './cart/cart';
import { Sidebar } from './sidebar/sidebar';
import { Stock } from './stock/stock';
import { Home } from './home/home';
import { Header } from './header/header';
import { CentralAdmin } from './central-admin/central-admin';
import { Invoice } from './invoice/invoice';

export const routes: Routes = [
    { path: 'register', component: Register },
    { path: 'products', component: Products },
    { path: 'dashboard', component: Dashboard },
    { path: 'login', component: Login },
    { path: 'admin', component: Admin },
    { path: 'central-admin', component: CentralAdmin },
    { path: 'user', component: User },
    { path: 'cart', component: Cart },
    { path: 'sidebar', component: Sidebar },
    { path: 'stock', component: Stock },
    { path: 'home', component: Home },
    { path: 'header', component: Header },
    { path: 'invoice', component: Invoice },
    { path: '**', redirectTo: 'dashboard', pathMatch: 'full' }
];
