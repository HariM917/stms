<!-- UsersDisplay.vue - Vue component for displaying users from the API -->

<template>
  <div class="users-display">
    <h2>STMS Users</h2>
    
    <!-- Error display -->
    <div v-if="error" class="error-message">
      <p>{{ error }}</p>
      <button @click="fetchUsers">Try Again</button>
    </div>
    
    <!-- Loading state -->
    <div v-if="loading" class="loading">
      <p>Loading users...</p>
    </div>
    
    <!-- Controls -->
    <div class="controls">
      <div class="search-box">
        <input 
          v-model="searchTerm" 
          type="text" 
          placeholder="Search users..."
        />
      </div>
      <button @click="fetchUsers" :disabled="loading" class="refresh-btn">
        {{ loading ? 'Loading...' : 'Refresh' }}
      </button>
    </div>
    
    <!-- Empty state -->
    <p v-if="!loading && !error && filteredUsers.length === 0" class="empty-state">
      No users found.
    </p>
    
    <!-- Users table -->
    <table v-if="!loading && filteredUsers.length > 0" class="users-table">
      <thead>
        <tr>
          <th @click="sortBy('id')" :class="{ active: sortKey === 'id' }">
            ID <span v-if="sortKey === 'id'">{{ sortOrder === 'asc' ? '↑' : '↓' }}</span>
          </th>
          <th @click="sortBy('name')" :class="{ active: sortKey === 'name' }">
            Name <span v-if="sortKey === 'name'">{{ sortOrder === 'asc' ? '↑' : '↓' }}</span>
          </th>
          <th @click="sortBy('email')" :class="{ active: sortKey === 'email' }">
            Email <span v-if="sortKey === 'email'">{{ sortOrder === 'asc' ? '↑' : '↓' }}</span>
          </th>
          <th @click="sortBy('role')" :class="{ active: sortKey === 'role' }">
            Role <span v-if="sortKey === 'role'">{{ sortOrder === 'asc' ? '↑' : '↓' }}</span>
          </th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="user in filteredUsers" :key="user.id">
          <td>{{ user.id }}</td>
          <td>{{ user.name }}</td>
          <td>{{ user.email }}</td>
          <td>
            <span class="role-badge" :class="user.role || 'user'">
              {{ user.role || 'user' }}
            </span>
          </td>
        </tr>
      </tbody>
    </table>

    <!-- Summary -->
    <div v-if="!loading && !error" class="summary">
      Showing {{ filteredUsers.length }} of {{ users.length }} users
    </div>
  </div>
</template>

<script>
export default {
  name: 'UsersDisplay',
  
  data() {
    return {
      users: [],
      loading: true,
      error: null,
      searchTerm: '',
      sortKey: 'name',
      sortOrder: 'asc'
    };
  },
  
  computed: {
    filteredUsers() {
      let result = this.users;
      
      // Apply search filter
      if (this.searchTerm) {
        const term = this.searchTerm.toLowerCase();
        result = result.filter(user => 
          user.name.toLowerCase().includes(term) || 
          user.email.toLowerCase().includes(term)
        );
      }
      
      // Apply sorting
      result = [...result].sort((a, b) => {
        let modifier = this.sortOrder === 'asc' ? 1 : -1;
        let aValue = a[this.sortKey] || '';
        let bValue = b[this.sortKey] || '';
        
        // Handle case-insensitive string comparison
        if (typeof aValue === 'string' && typeof bValue === 'string') {
          aValue = aValue.toLowerCase();
          bValue = bValue.toLowerCase();
        }
        
        if (aValue < bValue) return -1 * modifier;
        if (aValue > bValue) return 1 * modifier;
        return 0;
      });
      
      return result;
    }
  },
  
  created() {
    this.fetchUsers();
  },
  
  methods: {
    async fetchUsers() {
      this.loading = true;
      this.error = null;
      
      try {
        const token = (typeof localStorage !== 'undefined') ? (localStorage.getItem('token') || localStorage.getItem('stms_token')) : null;
        const headers = {};
        if (token) {
          headers['Authorization'] = `Bearer ${token}`;
        }
        const apiBase = (typeof window !== 'undefined' && window.location.origin ? window.location.origin : '') + '/api/v1';
        const response = await fetch(`${apiBase}/auth/users`, {
          headers,
          credentials: 'include'
        });
        
        if (!response.ok) {
          throw new Error(`HTTP error! Status: ${response.status}`);
        }
        
        const data = await response.json();
        
        if (!data.success) {
          throw new Error(data.message || 'API error');
        }
        
        this.users = data.users || [];
      } catch (error) {
        console.error('Error fetching users:', error);
        this.error = `Failed to load users: ${error.message}`;
      } finally {
        this.loading = false;
      }
    },
    
    sortBy(key) {
      // If already sorting by this key, toggle order
      if (this.sortKey === key) {
        this.sortOrder = this.sortOrder === 'asc' ? 'desc' : 'asc';
      } else {
        // New sort key, default to ascending
        this.sortKey = key;
        this.sortOrder = 'asc';
      }
    }
  }
};
</script>

<style scoped>
.users-display {
  font-family: Arial, sans-serif;
  max-width: 1000px;
  margin: 0 auto;
  padding: 20px;
}

h2 {
  color: #2c3e50;
  margin-bottom: 20px;
}

.error-message {
  background-color: #f8d7da;
  color: #721c24;
  padding: 10px 15px;
  border-radius: 4px;
  margin-bottom: 20px;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.error-message button {
  background-color: #dc3545;
  color: white;
  border: none;
  padding: 5px 10px;
  border-radius: 4px;
  cursor: pointer;
}

.loading {
  text-align: center;
  padding: 20px;
  color: #6c757d;
}

.controls {
  display: flex;
  justify-content: space-between;
  margin-bottom: 20px;
  align-items: center;
}

.search-box {
  flex-grow: 1;
  margin-right: 15px;
}

.search-box input {
  width: 100%;
  padding: 8px 12px;
  border: 1px solid #ced4da;
  border-radius: 4px;
  font-size: 14px;
}

.refresh-btn {
  background-color: #28a745;
  color: white;
  border: none;
  padding: 8px 15px;
  border-radius: 4px;
  cursor: pointer;
}

.refresh-btn:disabled {
  background-color: #6c757d;
  cursor: not-allowed;
}

.empty-state {
  text-align: center;
  padding: 30px;
  color: #6c757d;
  background-color: #f8f9fa;
  border-radius: 4px;
}

.users-table {
  width: 100%;
  border-collapse: collapse;
  margin-bottom: 20px;
}

.users-table th, .users-table td {
  padding: 12px 15px;
  text-align: left;
  border-bottom: 1px solid #dee2e6;
}

.users-table th {
  background-color: #f8f9fa;
  cursor: pointer;
}

.users-table th:hover {
  background-color: #e9ecef;
}

.users-table th.active {
  color: #007bff;
}

.users-table tbody tr:hover {
  background-color: #f8f9fa;
}

.role-badge {
  display: inline-block;
  padding: 4px 8px;
  border-radius: 12px;
  font-size: 12px;
  text-transform: capitalize;
}

.role-badge.admin {
  background-color: #f8d7da;
  color: #721c24;
}

.role-badge.user {
  background-color: #d1ecf1;
  color: #0c5460;
}

.role-badge.operator {
  background-color: #d4edda;
  color: #155724;
}

.role-badge.analyst {
  background-color: #fff3cd;
  color: #856404;
}

.summary {
  text-align: right;
  color: #6c757d;
  font-size: 14px;
  margin-top: 10px;
}

@media (max-width: 768px) {
  .controls {
    flex-direction: column;
  }
  
  .search-box {
    width: 100%;
    margin-right: 0;
    margin-bottom: 10px;
  }
  
  .users-table th, .users-table td {
    padding: 8px;
  }
}
</style>