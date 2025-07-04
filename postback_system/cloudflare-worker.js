/**
 * Cloudflare Workers脚本
 * 用于代理ByteC网络的Postback请求到后端服务器
 * 
 * 域名: https://network.bytec.com/involve/event
 * 目标: 转发到本地/生产环境的Postback系统
 */

// 配置常量
const CONFIG = {
    // 生产环境配置
    PRODUCTION: {
        enabled: false,  // 设置为true时使用生产环境
        endpoint: 'https://your-production-server.com/postback/involve/event',
    },
    
    // 开发环境配置 (ngrok等内网穿透工具)
    DEVELOPMENT: {
        enabled: true,   // 设置为true时使用开发环境
        endpoint: 'https://your-ngrok-url.ngrok.io/postback/involve/event',
        // 示例: 'https://abc123.ngrok.io/postback/involve/event'
    },
    
    // 备份配置
    FALLBACK: {
        endpoint: 'https://httpbin.org/anything',  // 测试用的端点
    },
    
    // 安全配置
    SECURITY: {
        allowedOrigins: ['*'],  // 生产环境中应该限制具体域名
        rateLimitPerMinute: 1000,
        requiredHeaders: [],
    }
};

// 速率限制缓存
const rateLimitCache = new Map();

/**
 * 主处理函数
 */
addEventListener('fetch', event => {
    event.respondWith(handleRequest(event.request));
});

/**
 * 处理传入的请求
 */
async function handleRequest(request) {
    const url = new URL(request.url);
    
    // 只处理 /involve/event 路径
    if (!url.pathname.startsWith('/involve/event')) {
        return new Response('Not Found', { status: 404 });
    }
    
    try {
        // 1. 安全检查
        const securityCheck = await performSecurityChecks(request);
        if (!securityCheck.allowed) {
            return new Response(securityCheck.reason, { status: securityCheck.status });
        }
        
        // 2. 速率限制检查
        const rateLimitCheck = await checkRateLimit(request);
        if (!rateLimitCheck.allowed) {
            return new Response('Rate Limit Exceeded', { status: 429 });
        }
        
        // 3. 确定目标端点
        const targetEndpoint = getTargetEndpoint();
        
        // 4. 构建代理请求
        const proxyRequest = buildProxyRequest(request, targetEndpoint, url);
        
        // 5. 发送请求到后端
        const response = await forwardRequest(proxyRequest);
        
        // 6. 添加响应头
        const finalResponse = addResponseHeaders(response);
        
        // 7. 记录请求日志
        await logRequest(request, response, targetEndpoint);
        
        return finalResponse;
        
    } catch (error) {
        console.error('Worker Error:', error);
        
        // 错误时的响应
        return new Response('Internal Server Error', {
            status: 500,
            headers: {
                'Content-Type': 'text/plain',
                'X-Error': error.message
            }
        });
    }
}

/**
 * 安全检查
 */
async function performSecurityChecks(request) {
    const url = new URL(request.url);
    
    // 检查请求方法
    if (!['GET', 'POST'].includes(request.method)) {
        return {
            allowed: false,
            status: 405,
            reason: 'Method Not Allowed'
        };
    }
    
    // 检查必需参数
    if (!url.searchParams.has('conversion_id')) {
        return {
            allowed: false,
            status: 400,
            reason: 'Missing required parameter: conversion_id'
        };
    }
    
    return { allowed: true };
}

/**
 * 速率限制检查
 */
async function checkRateLimit(request) {
    const clientIP = request.headers.get('CF-Connecting-IP') || 'unknown';
    const now = Math.floor(Date.now() / (60 * 1000)); // 每分钟
    const key = `${clientIP}_${now}`;
    
    const currentCount = rateLimitCache.get(key) || 0;
    
    if (currentCount >= CONFIG.SECURITY.rateLimitPerMinute) {
        return { allowed: false };
    }
    
    rateLimitCache.set(key, currentCount + 1);
    
    // 清理过期缓存
    setTimeout(() => rateLimitCache.delete(key), 60000);
    
    return { allowed: true };
}

/**
 * 确定目标端点
 */
function getTargetEndpoint() {
    if (CONFIG.PRODUCTION.enabled) {
        return CONFIG.PRODUCTION.endpoint;
    }
    
    if (CONFIG.DEVELOPMENT.enabled) {
        return CONFIG.DEVELOPMENT.endpoint;
    }
    
    return CONFIG.FALLBACK.endpoint;
}

/**
 * 构建代理请求
 */
function buildProxyRequest(originalRequest, targetEndpoint, originalUrl) {
    // 构建新的URL，保留所有查询参数
    const targetUrl = new URL(targetEndpoint);
    
    // 复制所有查询参数
    for (const [key, value] of originalUrl.searchParams) {
        targetUrl.searchParams.set(key, value);
    }
    
    // 复制请求头
    const headers = new Headers(originalRequest.headers);
    
    // 添加代理信息
    headers.set('X-Forwarded-For', originalRequest.headers.get('CF-Connecting-IP') || 'unknown');
    headers.set('X-Forwarded-Proto', 'https');
    headers.set('X-Forwarded-Host', originalUrl.hostname);
    headers.set('X-Original-URL', originalUrl.toString());
    headers.set('User-Agent', `CloudflareWorkers-ByteC-Proxy/1.0 ${headers.get('User-Agent') || ''}`);
    
    // 构建请求选项
    const requestOptions = {
        method: originalRequest.method,
        headers: headers,
    };
    
    // 如果是POST请求，复制请求体
    if (originalRequest.method === 'POST') {
        requestOptions.body = originalRequest.body;
    }
    
    return new Request(targetUrl.toString(), requestOptions);
}

/**
 * 转发请求到后端
 */
async function forwardRequest(proxyRequest) {
    try {
        const response = await fetch(proxyRequest, {
            timeout: 10000,  // 10秒超时
        });
        
        return response;
        
    } catch (error) {
        console.error('Forward Request Error:', error);
        
        // 返回友好的错误响应
        return new Response('Backend Service Unavailable', {
            status: 503,
            headers: {
                'Content-Type': 'text/plain',
                'X-Error-Type': 'Backend-Connection-Failed'
            }
        });
    }
}

/**
 * 添加响应头
 */
function addResponseHeaders(response) {
    const newResponse = new Response(response.body, {
        status: response.status,
        statusText: response.statusText,
        headers: response.headers
    });
    
    // 添加CORS头
    newResponse.headers.set('Access-Control-Allow-Origin', '*');
    newResponse.headers.set('Access-Control-Allow-Methods', 'GET, POST, OPTIONS');
    newResponse.headers.set('Access-Control-Allow-Headers', 'Content-Type, Authorization');
    
    // 添加安全头
    newResponse.headers.set('X-Frame-Options', 'DENY');
    newResponse.headers.set('X-Content-Type-Options', 'nosniff');
    
    // 添加代理标识
    newResponse.headers.set('X-Proxy-By', 'Cloudflare-Workers-ByteC');
    newResponse.headers.set('X-Proxy-Version', '1.0.0');
    
    return newResponse;
}

/**
 * 记录请求日志
 */
async function logRequest(request, response, targetEndpoint) {
    const logData = {
        timestamp: new Date().toISOString(),
        method: request.method,
        url: request.url,
        targetEndpoint: targetEndpoint,
        status: response.status,
        userAgent: request.headers.get('User-Agent'),
        clientIP: request.headers.get('CF-Connecting-IP'),
        country: request.cf?.country || 'unknown'
    };
    
    // 在实际生产环境中，可以将日志发送到日志服务
    console.log('ByteC Postback Proxy:', JSON.stringify(logData));
    
    // 可选：发送到外部日志服务
    // await sendToLogService(logData);
}

/**
 * 处理OPTIONS请求 (CORS预检)
 */
addEventListener('fetch', event => {
    if (event.request.method === 'OPTIONS') {
        event.respondWith(handleOptions());
    }
});

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