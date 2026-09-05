// React component example for using the Users API

import React, { useState, useEffect } from 'react';

// Define the API base URL - change as needed
const API_BASE_URL = (typeof window !== 'undefined' && window.location.origin ? window.location.origin : '') + '/api/v1';

/**
 * React component that displays users from the API
 */
function UsersList() {
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Fetch users when the component mounts
  useEffect(() => {
    fetchUsers();
  }, []);

  // Function to fetch users from the API
  const fetchUsers = async () => {
    setLoading(true);
    setError(null);

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

      // Update state with the users array
      setUsers(data.users || []);
    } catch (error) {
      console.error("Could not fetch users:", error);
      setError(error.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="users-list">
      <h2>System Users</h2>
      
      {/* Refresh button */}
      <button onClick={fetchUsers} disabled={loading}>
        {loading ? 'Loading...' : 'Refresh Users'}
      </button>
      
      {/* Show error if there is one */}
      {error && (
        <div className="error-message">
          Error: {error}
        </div>
      )}
      
      {/* Show loading indicator */}
      {loading && <div className="loading">Loading users...</div>}
      
      {/* Show users if they exist and we're not loading */}
      {!loading && !error && users.length === 0 && (
        <p>No users found.</p>
      )}
      
      {/* Display users in a table */}
      {!loading && !error && users.length > 0 && (
        <table className="users-table">
          <thead>
            <tr>
              <th>ID</th>
              <th>Name</th>
              <th>Email</th>
              <th>Role</th>
            </tr>
          </thead>
          <tbody>
            {users.map((user) => (
              <tr key={user.id}>
                <td>{user.id}</td>
                <td>{user.name}</td>
                <td>{user.email}</td>
                <td>{user.role || 'user'}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}

export default UsersList;