// Platform Configuration from .env
const PLATFORM_CONFIG = {
    // API Configuration
    API_BASE: 'http://localhost:8000',
    API_KEY: 'admin-key-456',
    ADMIN_TOKEN: 'local-admin-token',
    
    // Supabase Database
    SUPABASE_URL: 'https://your-supabase-project.supabase.co',
    SUPABASE_KEY: 'supabase_service_role_key_here',
    
    // Twilio (Voice & SMS)
    TWILIO_ACCOUNT_SID: 'ACXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX',
    TWILIO_AUTH_TOKEN: 'twilio_auth_token_goes_here',
    TWILIO_PHONE_NUMBER: '+12345678900',
    
    // Public URL for Webhooks
    BASE_URL: 'https://your-ngrok-or-public-url.example.com',
    
    // AI Providers
    DEEPGRAM_API_KEY: 'deepgram_api_key_here',
    GROQ_API_KEY: 'gsk_your_placeholder',
    OPENAI_API_KEY: 'sk-your-placeholder',
    ELEVENLABS_API_KEY: 'elevenlabs_api_key_here',
    
    // Integration Status (Pre-configured)
    INTEGRATIONS: {
        twilio: {
            name: 'Twilio',
            type: 'voice_sms',
            connected: true,
            account_sid: 'ACXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX',
            phone_number: '+12345678900'
        },
        deepgram: {
            name: 'Deepgram',
            type: 'speech_to_text',
            connected: true,
            status: 'Voice recognition enabled'
        },
        groq: {
            name: 'Groq',
            type: 'llm',
            connected: true,
            status: 'Fast inference enabled'
        },
        openai: {
            name: 'OpenAI',
            type: 'llm',
            connected: true,
            status: 'GPT models available'
        },
        elevenlabs: {
            name: 'ElevenLabs',
            type: 'text_to_speech',
            connected: true,
            status: 'Voice synthesis enabled'
        },
        supabase: {
            name: 'Supabase',
            type: 'database',
            connected: true,
            url: 'https://your-supabase-project.supabase.co'
        },
        ngrok: {
            name: 'Ngrok',
            type: 'tunnel',
            connected: true,
            url: 'https://your-ngrok-or-public-url.example.com'
        }
    }
};

// Helper function to mask sensitive keys
function maskApiKey(key) {
    if (!key || key.length < 8) return '••••••••';
    return key.substring(0, 4) + '••••••••' + key.substring(key.length - 4);
}

// Helper function to check if integration is connected
function isIntegrationConnected(integration) {
    return PLATFORM_CONFIG.INTEGRATIONS[integration]?.connected || false;
}

// Helper function to get integration status
function getIntegrationStatus(integration) {
    const config = PLATFORM_CONFIG.INTEGRATIONS[integration];
    if (!config) return { connected: false, message: 'Not configured' };
    return {
        connected: config.connected,
        message: config.status || (config.connected ? 'Connected' : 'Not connected')
    };
}
