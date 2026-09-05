// Type declarations for standalone Angular example components

declare module '@angular/core' {
  export function Injectable(options?: { providedIn?: string }): ClassDecorator;
  export function Component(options?: {
    selector?: string;
    templateUrl?: string;
    template?: string;
    styleUrls?: string[];
    styles?: string[];
  }): ClassDecorator;
  export interface OnInit {
    ngOnInit(): void;
  }
}

declare module '@angular/common/http' {
  export class HttpClient {
    get<T>(url: string, options?: Record<string, unknown>): import('rxjs').Observable<T>;
  }
  export class HttpErrorResponse {
    error: any;
    status: number;
    message: string;
  }
}

declare module 'rxjs' {
  export interface Observer<T> {
    next?: (value: T) => void;
    error?: (err: any) => void;
    complete?: () => void;
  }
  export interface Subscription {
    unsubscribe(): void;
  }
  export class Observable<T> {
    pipe<R>(...operations: any[]): Observable<R>;
    subscribe(observer?: Observer<T>): Subscription;
    subscribe(next?: (value: T) => void, error?: (error: any) => void, complete?: () => void): Subscription;
  }
  export function throwError(errorFactory: () => any): Observable<never>;
}

declare module 'rxjs/operators' {
  export function map<T, R>(project: (value: T, index: number) => R): (source: any) => any;
  export function catchError<T, R>(selector: (err: any, caught: any) => any): (source: any) => any;
}
