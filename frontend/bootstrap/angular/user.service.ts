// Angular service for Users API

import { Injectable } from '@angular/core';
import { HttpClient, HttpErrorResponse } from '@angular/common/http';
import { Observable, throwError } from 'rxjs';
import { catchError, map } from 'rxjs/operators';

// User interface
export interface User {
  id: string;
  name: string;
  email: string;
  role?: string;
}

// API response interface
interface ApiResponse<T> {
  success: boolean;
  count?: number;
  message?: string;
  users?: T[];
}

@Injectable({
  providedIn: 'root'
})
export class UserService {
  // API base URL - update this based on your environment
  private apiUrl = 'http://localhost:8001/api';

  constructor(private http: HttpClient) { }

  /**
   * Get all users from the API
   */
  getUsers(): Observable<User[]> {
    return this.http.get<ApiResponse<User>>(`${this.apiUrl}/users`)
      .pipe(
        map(response => {
          if (!response.success) {
            throw new Error(response.message || 'Failed to get users');
          }
          return response.users || [];
        }),
        catchError(this.handleError)
      );
  }

  /**
   * Error handler for HTTP requests
   */
  private handleError(error: HttpErrorResponse) {
    let errorMessage = 'An unknown error occurred';
    
    if (error.error instanceof ErrorEvent) {
      // Client-side error
      errorMessage = `Error: ${error.error.message}`;
    } else {
      // Server-side error
      errorMessage = `Error Code: ${error.status}\nMessage: ${error.message}`;
    }
    
    console.error(errorMessage);
    return throwError(() => new Error(errorMessage));
  }
}