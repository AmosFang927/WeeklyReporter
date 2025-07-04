/**
 * ByteC网络Postback代理 - Cloudflare Workers
 * 
 * 🎯 用途：将 https://network.bytec.com/involve/event 代理到后端Postback系统
 * 🔧 配置：支持开发/生产环境切换
 * 🚀 部署：可直接复制到Cloudflare Workers
 */

// ===== 配置设置 =====
const CONFIG = {
    // 🌍 环境配置
    ENVIRONMENT: 'development', // 'development' 或 'production'
    
    // 🔧 后端端点配置
    ENDPOINTS: {
        development: 'https://tex-graphic-status-windsor.trycloudflare.com/postback/involve/event',
        production: 'https://your-production-server.com/postback/involve/event',
        fallback: 'https://httpbin.org/anything'
    },
    
    // 🔒 安全配置
    SECURITY: {
        allowedOrigins: ['*'], // 生产环境中应限制具体域名
        rateLimitPerMinute: 500,
        requiredParams: ['conversion_id']
    },
    
    // 📊 日志配置
    LOGGING: {
        enabled: true,
        logLevel: 'info' // 'debug', 'info', 'warn', 'error'
    }
};

// ===== 主事件处理器 =====
addEventListener('fetch', event => {
    event.respondWith(handleRequest(event.request));
});

/**
 * 🚀 主请求处理函数
 */
async function handleRequest(request) {
    const startTime = Date.now();
    const url = new URL(request.url);
    
    // 📋 只处理 /involve/event 路径
    if (!url.pathname.includes('/involve/event')) {
        return createErrorResponse('Path not found', 404);
    }
    
    try {
        // 1️⃣ 安全检查
        const securityResult = validateRequest(request, url);
        if (!securityResult.valid) {
            return createErrorResponse(securityResult.error, securityResult.status);
        }
        
        // 2️⃣ 速率限制检查
        const rateLimitResult = await checkRateLimit(request);
        if (!rateLimitResult.allowed) {
            return createErrorResponse('Rate limit exceeded', 429);
        }
        
        // 3️⃣ 构建代理请求
        const proxyUrl = buildProxyUrl(url);
        const proxyRequest = buildProxyRequest(request, proxyUrl);
        
        // 4️⃣ 转发请求
        const response = await fetch(proxyRequest);
        
        // 5️⃣ 处理响应
        const finalResponse = processResponse(response);
        
        // 6️⃣ 记录日志
        await logRequest(request, response, proxyUrl, Date.now() - startTime);
        
        return finalResponse;
        
    } catch (error) {
        console.error('❌ Worker处理错误:', error);
        await logError(error, request, Date.now() - startTime);
        
        return createErrorResponse('Internal server error', 500, {
            'X-Error-Message': error.message,
            'X-Worker-Version': '1.0.0'
        });
    }
}

/**
 * 🔒 请求验证
 */
function validateRequest(request, url) {
    // 检查HTTP方法
    if (!['GET', 'POST'].includes(request.method)) {
        return { valid: false, error: 'Method not allowed', status: 405 };
    }
    
    // 检查必需参数
    for (const param of CONFIG.SECURITY.requiredParams) {
        if (!url.searchParams.has(param)) {
            return { valid: false, error: `Missing required parameter: ${param}`, status: 400 };
        }
    }
    
    return { valid: true };
}

/**
 * ⚡ 速率限制检查
 */
async function checkRateLimit(request) {
    // 简化版速率限制（生产环境建议使用Durable Objects）
    const clientIP = request.headers.get('CF-Connecting-IP') || 'unknown';
    
    // 这里可以添加更复杂的速率限制逻辑
    // 目前直接返回允许
    return { allowed: true, remaining: CONFIG.SECURITY.rateLimitPerMinute };
}

/**
 * 🔗 构建代理URL
 */
function buildProxyUrl(originalUrl) {
    const endpoint = CONFIG.ENDPOINTS[CONFIG.ENVIRONMENT] || CONFIG.ENDPOINTS.fallback;
    const proxyUrl = new URL(endpoint);
    
    // 复制所有查询参数
    for (const [key, value] of originalUrl.searchParams) {
        proxyUrl.searchParams.set(key, value);
    }
    
    return proxyUrl.toString();
}

/**
 * 📦 构建代理请求
 */
function buildProxyRequest(originalRequest, proxyUrl) {
    const headers = new Headers(originalRequest.headers);
    
    // 添加代理标识头
    headers.set('X-Forwarded-For', originalRequest.headers.get('CF-Connecting-IP') || 'unknown');
    headers.set('X-Forwarded-Proto', 'https');
    headers.set('X-Forwarded-Host', new URL(originalRequest.url).hostname);
    headers.set('X-Original-URL', originalRequest.url);
    headers.set('X-Worker-Proxy', 'ByteC-Network-v1.0');
    
    const requestInit = {
        method: originalRequest.method,
        headers: headers,
    };
    
    // 如果是POST请求，复制请求体
    if (originalRequest.method === 'POST') {
        requestInit.body = originalRequest.body;
    }
    
    return new Request(proxyUrl, requestInit);
}

/**
 * 📤 处理响应
 */
function processResponse(response) {
    // 创建新的响应以添加CORS头
    const newResponse = new Response(response.body, {
        status: response.status,
        statusText: response.statusText,
        headers: response.headers
    });
    
    // 添加CORS头
    newResponse.headers.set('Access-Control-Allow-Origin', '*');
    newResponse.headers.set('Access-Control-Allow-Methods', 'GET, POST, OPTIONS');
    newResponse.headers.set('Access-Control-Allow-Headers', 'Content-Type, Authorization');
    
    // 添加代理标识
    newResponse.headers.set('X-Powered-By', 'Cloudflare-Workers');
    newResponse.headers.set('X-ByteC-Proxy', 'Active');
    
    return newResponse;
}

/**
 * ❌ 创建错误响应
 */
function createErrorResponse(message, status, extraHeaders = {}) {
    const headers = {
        'Content-Type': 'text/plain',
        'Access-Control-Allow-Origin': '*',
        'X-Error': 'true',
        ...extraHeaders
    };
    
    return new Response(message, { status, headers });
}

/**
 * 📊 记录请求日志
 */
async function logRequest(request, response, proxyUrl, duration) {
    if (!CONFIG.LOGGING.enabled) return;
    
    const logData = {
        timestamp: new Date().toISOString(),
        method: request.method,
        url: request.url,
        proxyUrl: proxyUrl,
        status: response.status,
        duration: `${duration}ms`,
        userAgent: request.headers.get('User-Agent') || 'unknown',
        ip: request.headers.get('CF-Connecting-IP') || 'unknown',
        country: request.headers.get('CF-IPCountry') || 'unknown'
    };
    
    console.log('📊 请求日志:', JSON.stringify(logData));
}

/**
 * ⚠️ 记录错误日志
 */
async function logError(error, request, duration) {
    const errorLog = {
        timestamp: new Date().toISOString(),
        error: error.message,
        stack: error.stack,
        url: request.url,
        method: request.method,
        duration: `${duration}ms`
    };
    
    console.error('❌ 错误日志:', JSON.stringify(errorLog));
}

/**
 * 🎯 处理OPTIONS请求（CORS预检）
 */
function handleOptions() {
    return new Response(null, {
        status: 200,
        headers: {
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
            'Access-Control-Allow-Headers': 'Content-Type, Authorization',
            'Access-Control-Max-Age': '86400'
        }
    });
} 