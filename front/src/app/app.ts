import { Component, OnInit, signal } from '@angular/core';
import { RouterOutlet } from '@angular/router';
import { Header } from './header/header';
import { Sidebar } from './sidebar/sidebar';
import { AuthService } from './services/auth.service';

@Component({
  selector: 'app-root',
  imports: [RouterOutlet, Header, Sidebar],
  templateUrl: './app.html',
  styleUrl: './app.css'
})
export class App implements OnInit {
  protected readonly title = signal('store');

  constructor(private authService: AuthService) {}

  ngOnInit(): void {
    if (this.authService.token()) {
      this.authService.loadCurrentUser().subscribe({
        error: (err) => {
          if (err?.status === 401) {
            this.authService.logout();
          }
        },
      });
    }
  }
  
  protected readonly isDarkMode = signal(false);

  toggleTheme(): void {
    this.isDarkMode.set(!this.isDarkMode());
  }
}
