### 1. Configuration

Before running the server, configure it using the built-in configurator:

- Run quickconfig

This launches an interactive menu where you can:

- Set server port (default: 5000)
- Configure CORS origins
- Add user accounts with passwords
- Manage server settings

### 2. Running the Server

- Run quickserve

The server will start and display access URLs for both local computer and network access.

To use the official web interface at `https://quickserve.8gudbits.qzz.io`, you must allow it as a CORS origin in your configuration (default):

1. Run quickconfig
2. Select "Manage CORS Origins"
3. Add `https://quickserve.8gudbits.qzz.io` to allowed origins

-- OR -- Self-Hosted Frontend

Alternatively, you can host the frontend files yourself:

1. Download the QuickServe repository from github
2. Serve the `frontend/` directory with any web server
3. Add your frontend URL to CORS origins in the configuration
4. Access your self-hosted interface instead

### Security Notes

- CORS origins should be properly configured for use
- Default configuration allows only [official login portal](https://8gudbits.github.io/quickserve.8gudbits/login)

