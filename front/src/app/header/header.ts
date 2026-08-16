import { Component, ElementRef, EventEmitter, HostBinding, HostListener, input, output, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router } from '@angular/router';
import { AuthService } from '../services/auth.service';

@Component({
  selector: 'app-header',
  imports: [CommonModule],
  templateUrl: './header.html',
  styleUrl: './header.css',
})
export class Header {
  public darkMode = false;

  isDarkMode(): boolean {
    return this.darkMode;
  }

  toggleTheme(): void {
    this.darkMode = !this.darkMode;

    // Apply/remove class on the root element
    const appShell = document.querySelector('.app-shell');
    if (appShell) {
      if (this.darkMode) {
        appShell.classList.add('dark-theme');
      } else {
        appShell.classList.remove('dark-theme');
      }
    }
  }

  constructor(public authService: AuthService, private router: Router, private eRef: ElementRef) {}

  toggleSidebar() {
    try {
      document.body.classList.toggle('sidebar-collapsed');
    } 
    catch (e) {
      // no-op for server-side or test environments
    }
  }

  isOpen = false;

  toggleDropdown() {
    this.isOpen = !this.isOpen;
  }

  closeDropdown() {
    this.isOpen = false;
  }

  logout(): void {
    this.authService.logout();
    this.router.navigate(['/login']);
  }

  @HostListener('document:click', ['$event'])
  handleClickOutside(event: Event) {
    if (!this.isOpen && !this.eRef.nativeElement.contains(event.target)) {
      this.closeDropdown();
    }
  }

}
