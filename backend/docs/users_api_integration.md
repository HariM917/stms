# STMS Users API Integration Guide

This document provides guidance on integrating the Smart Traffic Management System (STMS) Users API into various frontend frameworks and applications.

## API Endpoint

The Users API endpoint is available at:

```
GET http://localhost:8001/api/users
```

Response format:

```json
{
  "success": true,
  "count": 1,
  "users": [
    {
      "id": "user_123",
      "name": "Demo User",
      "email": "demo@example.com",
      "role": "user"
    }
  ]
}
```

## Integration Options

We've provided several examples of how to integrate the Users API with different frontend frameworks:

### 1. Vanilla JavaScript

The simplest way to integrate the Users API is using our pre-built JavaScript library:

```html
<link rel="stylesheet" href="./css/UsersAPI.css">
<div id="users-container"></div>
<script src="./js/UsersAPI.js"></script>
<script>
  const api = new STMSUsersAPI('http://localhost:8001');
  const container = document.getElementById('users-container');
  api.renderUsers(container);
</script>
```

See the full example in `frontend/users-example.html`

### 2. React Component

For React applications, we provide a ready-to-use component:

```jsx
import React from 'react';
import UsersList from './js/UsersListComponent';

function App() {
  return (
    <div className="App">
      <header className="App-header">
        <h1>STMS Dashboard</h1>
      </header>
      <main>
        <UsersList />
      </main>
    </div>
  );
}

export default App;
```

See the full implementation in `frontend/js/UsersListComponent.jsx`

### 3. Vue.js Component

For Vue.js applications:

```vue
<template>
  <div id="app">
    <header>
      <h1>STMS Dashboard</h1>
    </header>
    <UsersDisplay />
  </div>
</template>

<script>
import UsersDisplay from './UsersDisplay.vue'

export default {
  name: 'App',
  components: {
    UsersDisplay
  }
}
</script>
```

See the full implementation in `frontend/vue/UsersDisplay.vue`

### 4. Angular Integration

For Angular applications:

1. Include the service in your app module:

```typescript
import { BrowserModule } from '@angular/platform-browser';
import { NgModule } from '@angular/core';
import { HttpClientModule } from '@angular/common/http';
import { UserService } from './user.service';
import { AppComponent } from './app.component';
import { UsersListComponent } from './users-list.component';

@NgModule({
  declarations: [
    AppComponent,
    UsersListComponent
  ],
  imports: [
    BrowserModule,
    HttpClientModule
  ],
  providers: [UserService],
  bootstrap: [AppComponent]
})
export class AppModule { }
```

2. Use the component in your templates:

```html
<app-users-list></app-users-list>
```

See the full implementation in the Angular files:
- `frontend/angular/user.service.ts`
- `frontend/angular/users-list.component.ts`
- `frontend/angular/users-list.component.html`
- `frontend/angular/users-list.component.scss`

## Custom Implementation

If you need to create your own custom implementation, here's a simple fetch example:

```javascript
async function fetchUsers() {
  try {
    const response = await fetch('http://localhost:8001/api/users');
    
    if (!response.ok) {
      throw new Error(`HTTP error! Status: ${response.status}`);
    }
    
    const data = await response.json();
    
    if (!data.success) {
      throw new Error(data.message || 'Unknown API error');
    }
    
    return data.users || [];
  } catch (error) {
    console.error("Error fetching users:", error);
    throw error;
  }
}
```

## Testing the API

You can test the Users API endpoint using the provided test script:

```bash
python direct_api_test.py
```

This script will test various API endpoints including the Users API and generate a report in `api_test_results.txt`.

## User Object Structure

Each user object contains the following properties:

- `id` (string): Unique identifier for the user
- `name` (string): Display name of the user
- `email` (string): Email address (also used for login)
- `role` (string): User role (e.g., "user", "admin", "operator")

## Extending the API

The current implementation is a demonstration with an in-memory database. To extend this for production use:

1. Implement proper database storage (e.g., SQL, MongoDB)
2. Add user creation and management endpoints (POST, PUT, DELETE methods)
3. Implement proper authentication and authorization
4. Add input validation and error handling

## Support

For questions or support regarding the Users API, please contact the STMS team or refer to the documentation in the `docs` folder.