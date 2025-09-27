/**
 * JWT Authentication Middleware for API Gateway
 * Handles WebSocket and HTTP authentication with JWT tokens
 */

const jwt = require('jsonwebtoken');
const logger = require('../utils/logger');

class AuthMiddleware {
    constructor(config) {
        this.config = {
            jwtSecret: config.jwtSecret || process.env.JWT_SECRET || 'your-secret-key',
            jwtExpiresIn: config.jwtExpiresIn || '24h',
            algorithms: ['HS256'],
            issuer: 'api-gateway',
            audience: 'suho-trading',
            ...config
        };

        if (!this.config.jwtSecret || this.config.jwtSecret === 'your-secret-key') {
            logger.warn('Using default JWT secret. Please set JWT_SECRET environment variable for production.');
        }
    }

    /**
     * HTTP Authentication Middleware
     */
    authenticateHTTP() {
        return async (req, res, next) => {
            try {
                const token = this.extractTokenFromRequest(req);

                if (!token) {
                    return res.status(401).json({
                        error: 'Authentication required',
                        code: 'NO_TOKEN'
                    });
                }

                const decoded = await this.verifyToken(token);
                req.user = decoded;
                req.userContext = this.extractUserContext(decoded);

                logger.debug('HTTP request authenticated', {
                    userId: req.userContext.userId,
                    method: req.method,
                    path: req.path
                });

                next();
            } catch (error) {
                logger.warn('HTTP authentication failed', {
                    error: error.message,
                    path: req.path,
                    ip: req.ip
                });

                return res.status(401).json({
                    error: 'Authentication failed',
                    code: 'INVALID_TOKEN',
                    message: error.message
                });
            }
        };
    }

    /**
     * WebSocket Authentication
     */
    async authenticateWebSocket(request) {
        try {
            const token = this.extractTokenFromWebSocket(request);

            if (!token) {
                return {
                    success: false,
                    error: 'Authentication token required',
                    code: 'NO_TOKEN'
                };
            }

            const decoded = await this.verifyToken(token);
            const userContext = this.extractUserContext(decoded);

            // Additional WebSocket-specific validations
            const validationResult = await this.validateWebSocketPermissions(userContext);
            if (!validationResult.valid) {
                return {
                    success: false,
                    error: validationResult.error,
                    code: 'INSUFFICIENT_PERMISSIONS'
                };
            }

            logger.info('WebSocket authentication successful', {
                userId: userContext.userId,
                subscriptionTier: userContext.subscriptionTier,
                ip: request.socket.remoteAddress
            });

            return {
                success: true,
                userContext,
                user: decoded
            };

        } catch (error) {
            logger.warn('WebSocket authentication failed', {
                error: error.message,
                ip: request.socket?.remoteAddress
            });

            return {
                success: false,
                error: 'Invalid authentication token',
                code: 'INVALID_TOKEN'
            };
        }
    }

    /**
     * Extract token from HTTP request
     */
    extractTokenFromRequest(req) {
        // Check Authorization header
        const authHeader = req.headers.authorization;
        if (authHeader && authHeader.startsWith('Bearer ')) {
            return authHeader.substring(7);
        }

        // Check query parameter
        if (req.query.token) {
            return req.query.token;
        }

        // Check cookie
        if (req.cookies && req.cookies.auth_token) {
            return req.cookies.auth_token;
        }

        return null;
    }

    /**
     * Extract token from WebSocket request
     */
    extractTokenFromWebSocket(request) {
        try {
            const url = new URL(request.url, 'ws://localhost');

            // Check query parameter
            const token = url.searchParams.get('token');
            if (token) {
                return token;
            }

            // Check Authorization header
            const authHeader = request.headers.authorization;
            if (authHeader && authHeader.startsWith('Bearer ')) {
                return authHeader.substring(7);
            }

            // Check custom header
            if (request.headers['x-auth-token']) {
                return request.headers['x-auth-token'];
            }

            return null;
        } catch (error) {
            logger.error('Error extracting WebSocket token', { error });
            return null;
        }
    }

    /**
     * Verify JWT token
     */
    async verifyToken(token) {
        try {
            const decoded = jwt.verify(token, this.config.jwtSecret, {
                algorithms: this.config.algorithms,
                issuer: this.config.issuer,
                audience: this.config.audience
            });

            // Check if token is expired
            const now = Math.floor(Date.now() / 1000);
            if (decoded.exp && decoded.exp < now) {
                throw new Error('Token expired');
            }

            return decoded;
        } catch (error) {
            if (error.name === 'TokenExpiredError') {
                throw new Error('Token expired');
            } else if (error.name === 'JsonWebTokenError') {
                throw new Error('Invalid token');
            } else if (error.name === 'NotBeforeError') {
                throw new Error('Token not active');
            } else {
                throw new Error('Token verification failed');
            }
        }
    }

    /**
     * Extract user context from decoded token
     */
    extractUserContext(decoded) {
        return {
            userId: decoded.sub || decoded.user_id,
            companyId: decoded.company_id,
            subscriptionTier: decoded.subscription_tier || 'free',
            permissions: decoded.permissions || [],
            email: decoded.email,
            firstName: decoded.first_name,
            lastName: decoded.last_name,
            iat: decoded.iat,
            exp: decoded.exp
        };
    }

    /**
     * Validate WebSocket-specific permissions
     */
    async validateWebSocketPermissions(userContext) {
        // Check if user has MT5 trading permission
        const requiredPermissions = ['mt5_trading', 'websocket_access'];
        const hasPermission = requiredPermissions.some(permission =>
            userContext.permissions.includes(permission) ||
            userContext.permissions.includes('admin')
        );

        if (!hasPermission) {
            return {
                valid: false,
                error: 'Insufficient permissions for WebSocket access'
            };
        }

        // Check subscription tier limits
        const tierLimits = {
            free: { maxConnections: 2 },
            pro: { maxConnections: 10 },
            enterprise: { maxConnections: 50 }
        };

        const userTier = userContext.subscriptionTier || 'free';
        const limits = tierLimits[userTier] || tierLimits.free;

        // Additional validations can be added here
        // For example, check current connection count

        return { valid: true, limits };
    }

    /**
     * Generate JWT token
     */
    generateToken(payload) {
        const tokenPayload = {
            ...payload,
            iss: this.config.issuer,
            aud: this.config.audience,
            iat: Math.floor(Date.now() / 1000)
        };

        return jwt.sign(tokenPayload, this.config.jwtSecret, {
            expiresIn: this.config.jwtExpiresIn,
            algorithm: 'HS256'
        });
    }

    /**
     * Generate refresh token
     */
    generateRefreshToken(userId) {
        return jwt.sign(
            {
                sub: userId,
                type: 'refresh',
                iss: this.config.issuer,
                aud: this.config.audience
            },
            this.config.jwtSecret,
            {
                expiresIn: '7d',
                algorithm: 'HS256'
            }
        );
    }

    /**
     * Refresh access token
     */
    async refreshAccessToken(refreshToken) {
        try {
            const decoded = jwt.verify(refreshToken, this.config.jwtSecret);

            if (decoded.type !== 'refresh') {
                throw new Error('Invalid refresh token');
            }

            // Here you would typically fetch user data from database
            // For now, we'll use the userId from the refresh token
            const newTokenPayload = {
                sub: decoded.sub,
                type: 'access'
            };

            return this.generateToken(newTokenPayload);
        } catch (error) {
            throw new Error('Invalid refresh token');
        }
    }

    /**
     * Middleware for optional authentication
     */
    optionalAuth() {
        return async (req, res, next) => {
            try {
                const token = this.extractTokenFromRequest(req);
                if (token) {
                    const decoded = await this.verifyToken(token);
                    req.user = decoded;
                    req.userContext = this.extractUserContext(decoded);
                }
            } catch (error) {
                // Log but don't fail for optional auth
                logger.debug('Optional auth failed', { error: error.message });
            }

            next();
        };
    }
}

module.exports = AuthMiddleware;