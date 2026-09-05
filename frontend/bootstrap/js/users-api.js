// Example JavaScript code to use the users API

// Define the API base URL - change as needed
const API_BASE_URL = (typeof window !== 'undefined' && window.location.origin ? window.location.origin : '') + '/api/v1';

/**
 * Fetch users from the API
 * @returns {Promise<Array>} - Promise that resolves to array of users
 */
async function fetchUsers() {
  try {
    const token = (typeof localStorage !== 'undefined') ? (localStorage.getItem('token') || localStorage.getItem('stms_token')) : null;
    const headers = {};
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }
    // Send a GET request to the backend's API endpoint
    const response = await fetch(`${API_BASE_URL}/auth/users`, {
      headers,
      credentials: 'include'
    });

    // Check if the response was successful (status code 200-299)
    if (!response.ok) {
      throw new Error(`HTTP error! Status: ${response.status}`);
    }

    // Parse the JSON data from the response
    const data = await response.json();

    // Check if the request was successful according to our API convention
    if (!data.success) {
      throw new Error(data.message || 'Unknown API error');
    }

    // Return the users array
    return data.users || [];
  } catch (error) {
    console.error("Could not fetch users:", error);
    throw error;
  }
}

/**
 * Display users in the UI
 * @param {string} elementId - ID of the element to populate with users
 */
async function displayUsers(elementId) {
  const element = document.getElementById(elementId);
  if (!element) {
    console.error(`Element with ID '${elementId}' not found`);
    return;
  }

  try {
    element.innerHTML = '<p>Loading users...</p>';
    
    // Fetch users
    const users = await fetchUsers();
    
    if (users.length === 0) {
      element.innerHTML = '<p>No users found.</p>';
      return;
    }
    
    // Create a table to display users
    const table = document.createElement('table');
    table.innerHTML = `
      <thead>
        <tr>
          <th>ID</th>
          <th>Name</th>
          <th>Email</th>
          <th>Role</th>
        </tr>
      </thead>
      <tbody>
        ${users.map(user => `
          <tr>
            <td>${user.id}</td>
            <td>${user.name}</td>
            <td>${user.email}</td>
            <td>${user.role || 'user'}</td>
          </tr>
        `).join('')}
      </tbody>
    `;
    
    // Clear the element and append the table
    element.innerHTML = '';
    element.appendChild(table);
    
  } catch (error) {
    element.innerHTML = `<p class="error">Error loading users: ${error.message}</p>`;
  }
}

// Usage example:
// document.addEventListener('DOMContentLoaded', () => {
//   displayUsers('usersList');
// });

// Export functions for use in other scripts
if (typeof module !== 'undefined' && module.exports) {
  module.exports = {
    fetchUsers,
    displayUsers
  };
}