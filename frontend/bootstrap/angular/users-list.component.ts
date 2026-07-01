// Angular component for Users List

import { Component, OnInit } from '@angular/core';
import { UserService, User } from './user.service';

@Component({
  selector: 'app-users-list',
  templateUrl: './users-list.component.html',
  styleUrls: ['./users-list.component.scss']
})
export class UsersListComponent implements OnInit {
  users: User[] = [];
  filteredUsers: User[] = [];
  loading = true;
  error: string | null = null;
  searchTerm = '';
  sortColumn = 'name';
  sortDirection = 'asc';

  constructor(private userService: UserService) { }

  ngOnInit(): void {
    this.loadUsers();
  }

  /**
   * Load users from the service
   */
  loadUsers(): void {
    this.loading = true;
    this.error = null;

    this.userService.getUsers().subscribe({
      next: (data) => {
        this.users = data;
        this.applyFilters();
        this.loading = false;
      },
      error: (error) => {
        this.error = error.message;
        this.loading = false;
      }
    });
  }

  /**
   * Filter users based on search term
   */
  applyFilters(): void {
    let filtered = [...this.users];
    
    // Apply search filter
    if (this.searchTerm) {
      const term = this.searchTerm.toLowerCase();
      filtered = filtered.filter(user => 
        user.name.toLowerCase().includes(term) || 
        user.email.toLowerCase().includes(term) ||
        (user.role && user.role.toLowerCase().includes(term))
      );
    }
    
    // Apply sorting
    filtered = this.sortUsers(filtered);
    
    this.filteredUsers = filtered;
  }

  /**
   * Sort users based on current sort column and direction
   */
  sortUsers(users: User[]): User[] {
    return [...users].sort((a, b) => {
      const column = this.sortColumn as keyof User;
      const direction = this.sortDirection === 'asc' ? 1 : -1;
      
      const aVal = (a[column] || '') as string;
      const bVal = (b[column] || '') as string;
      
      return direction * aVal.localeCompare(bVal);
    });
  }

  /**
   * Set sorting column and direction
   */
  sortBy(column: string): void {
    if (this.sortColumn === column) {
      // Toggle direction if already sorting by this column
      this.sortDirection = this.sortDirection === 'asc' ? 'desc' : 'asc';
    } else {
      // Set new column and default to ascending
      this.sortColumn = column;
      this.sortDirection = 'asc';
    }
    
    this.applyFilters();
  }

  /**
   * Handle search input changes
   */
  onSearchChange(event: Event): void {
    this.searchTerm = (event.target as HTMLInputElement).value;
    this.applyFilters();
  }
}