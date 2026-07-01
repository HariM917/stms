/**
 * UsersAPI.js
 * A vanilla JavaScript library for working with the STMS Users API
 */

class STMSUsersAPI {
  /**
   * Initialize the API client
   * @param {string} baseUrl - Base URL of the API (default: http://localhost:8001)
   */
  constructor(baseUrl = 'http://localhost:8001') {
    this.baseUrl = baseUrl;
    this.endpoints = {
      users: `${this.baseUrl}/api/users`
    };
  }

  /**
   * Get all users from the API
   * @returns {Promise<Object>} Promise resolving to the users data
   */
  async getUsers() {
    try {
      const response = await fetch(this.endpoints.users);
      
      if (!response.ok) {
        throw new Error(`HTTP error! Status: ${response.status}`);
      }
      
      const data = await response.json();
      
      if (!data.success) {
        throw new Error(data.message || 'API returned an error');
      }
      
      return {
        success: true,
        users: data.users || [],
        count: data.count || 0
      };
    } catch (error) {
      console.error('Error fetching users:', error);
      return {
        success: false,
        error: error.message,
        users: []
      };
    }
  }
  
  /**
   * Render users to a HTML element
   * @param {HTMLElement} containerElement - The DOM element to render users in
   * @param {Object} options - Rendering options
   */
  async renderUsers(containerElement, options = {}) {
    if (!containerElement) {
      console.error('Container element is required');
      return;
    }
    
    // Default options
    const defaultOptions = {
      title: 'System Users',
      showRefreshButton: true,
      showSearch: true,
      tableClasses: 'stms-users-table',
      loadingMessage: 'Loading users...',
      noUsersMessage: 'No users found',
      errorMessage: 'Failed to load users'
    };
    
    const settings = { ...defaultOptions, ...options };
    
    // Create UI structure
    containerElement.innerHTML = `
      <div class="stms-users-container">
        <h2>${settings.title}</h2>
        <div class="stms-users-error" style="display: none;"></div>
        
        <div class="stms-users-controls">
          ${settings.showSearch ? `
            <div class="stms-search-container">
              <input type="text" class="stms-search-input" placeholder="Search users...">
            </div>
          ` : ''}
          
          ${settings.showRefreshButton ? `
            <button class="stms-refresh-btn">Refresh</button>
          ` : ''}
        </div>
        
        <div class="stms-users-loading">${settings.loadingMessage}</div>
        <div class="stms-users-empty" style="display: none;">${settings.noUsersMessage}</div>
        
        <div class="stms-users-table-container" style="display: none;">
          <table class="${settings.tableClasses}">
            <thead>
              <tr>
                <th data-sort="id">ID</th>
                <th data-sort="name">Name</th>
                <th data-sort="email">Email</th>
                <th data-sort="role">Role</th>
              </tr>
            </thead>
            <tbody></tbody>
          </table>
        </div>
      </div>
    `;
    
    // Cache DOM elements
    const elements = {
      container: containerElement.querySelector('.stms-users-container'),
      error: containerElement.querySelector('.stms-users-error'),
      controls: containerElement.querySelector('.stms-users-controls'),
      searchInput: containerElement.querySelector('.stms-search-input'),
      refreshBtn: containerElement.querySelector('.stms-refresh-btn'),
      loading: containerElement.querySelector('.stms-users-loading'),
      empty: containerElement.querySelector('.stms-users-empty'),
      tableContainer: containerElement.querySelector('.stms-users-table-container'),
      table: containerElement.querySelector('table'),
      tableBody: containerElement.querySelector('table tbody'),
      tableHeaders: containerElement.querySelectorAll('th[data-sort]')
    };
    
    // State
    const state = {
      users: [],
      filteredUsers: [],
      sortColumn: 'name',
      sortDirection: 'asc',
      searchTerm: ''
    };
    
    // Add event listeners
    if (elements.refreshBtn) {
      elements.refreshBtn.addEventListener('click', loadUsers);
    }
    
    if (elements.searchInput) {
      elements.searchInput.addEventListener('input', (e) => {
        state.searchTerm = e.target.value.toLowerCase();
        filterAndRenderUsers();
      });
    }
    
    if (elements.tableHeaders) {
      elements.tableHeaders.forEach(header => {
        header.addEventListener('click', () => {
          const column = header.getAttribute('data-sort');
          if (state.sortColumn === column) {
            // Toggle direction
            state.sortDirection = state.sortDirection === 'asc' ? 'desc' : 'asc';
          } else {
            state.sortColumn = column;
            state.sortDirection = 'asc';
          }
          
          // Update header appearance
          elements.tableHeaders.forEach(h => h.classList.remove('sorted-asc', 'sorted-desc'));
          header.classList.add(`sorted-${state.sortDirection}`);
          
          filterAndRenderUsers();
        });
      });
    }
    
    // Load users
    loadUsers();
    
    // Function to load users from API
    async function loadUsers() {
      showLoading(true);
      showError(false);
      
      const result = await new STMSUsersAPI(options.baseUrl).getUsers();
      
      if (result.success) {
        state.users = result.users;
        filterAndRenderUsers();
      } else {
        showError(true, result.error || settings.errorMessage);
      }
      
      showLoading(false);
    }
    
    // Function to filter and render users
    function filterAndRenderUsers() {
      // Filter
      if (state.searchTerm) {
        state.filteredUsers = state.users.filter(user => 
          user.name.toLowerCase().includes(state.searchTerm) ||
          user.email.toLowerCase().includes(state.searchTerm) ||
          (user.role && user.role.toLowerCase().includes(state.searchTerm))
        );
      } else {
        state.filteredUsers = [...state.users];
      }
      
      // Sort
      state.filteredUsers.sort((a, b) => {
        const column = state.sortColumn;
        const direction = state.sortDirection === 'asc' ? 1 : -1;
        
        const aVal = (a[column] || '').toString().toLowerCase();
        const bVal = (b[column] || '').toString().toLowerCase();
        
        return direction * aVal.localeCompare(bVal);
      });
      
      // Show empty message if no results
      if (state.filteredUsers.length === 0) {
        elements.empty.style.display = 'block';
        elements.tableContainer.style.display = 'none';
      } else {
        elements.empty.style.display = 'none';
        elements.tableContainer.style.display = 'block';
        renderTable();
      }
    }
    
    // Function to render the table
    function renderTable() {
      elements.tableBody.innerHTML = '';
      
      state.filteredUsers.forEach(user => {
        const row = document.createElement('tr');
        
        // ID cell
        const idCell = document.createElement('td');
        idCell.textContent = user.id;
        row.appendChild(idCell);
        
        // Name cell
        const nameCell = document.createElement('td');
        nameCell.textContent = user.name;
        row.appendChild(nameCell);
        
        // Email cell
        const emailCell = document.createElement('td');
        emailCell.textContent = user.email;
        row.appendChild(emailCell);
        
        // Role cell
        const roleCell = document.createElement('td');
        const role = user.role || 'user';
        const roleBadge = document.createElement('span');
        roleBadge.className = `role-badge ${role}`;
        roleBadge.textContent = role;
        roleCell.appendChild(roleBadge);
        row.appendChild(roleCell);
        
        elements.tableBody.appendChild(row);
      });
    }
    
    // Function to show/hide loading indicator
    function showLoading(isLoading) {
      elements.loading.style.display = isLoading ? 'block' : 'none';
    }
    
    // Function to show/hide error message
    function showError(isError, message = '') {
      elements.error.style.display = isError ? 'block' : 'none';
      if (isError) {
        elements.error.innerHTML = `
          <p>${message}</p>
          <button>Try Again</button>
        `;
        elements.error.querySelector('button').addEventListener('click', loadUsers);
      }
    }
    
    // Return API for chaining
    return this;
  }
}

// Add to global scope if in browser environment
if (typeof window !== 'undefined') {
  window.STMSUsersAPI = STMSUsersAPI;
}