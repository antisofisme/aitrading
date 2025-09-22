const TelegramBot = require('node-telegram-bot-api');
const winston = require('winston');
const { getUserTelegramSettings, updateUserTelegramSettings } = require('./userNotificationService');

const logger = winston.createLogger({
  level: 'info',
  format: winston.format.json(),
  defaultMeta: { service: 'notification-service-telegram' }
});

// Telegram bot configuration
const BOT_TOKEN = process.env.TELEGRAM_BOT_TOKEN;
const WEBHOOK_URL = process.env.TELEGRAM_WEBHOOK_URL;
const WEBHOOK_SECRET = process.env.TELEGRAM_WEBHOOK_SECRET;

let bot;
let isPolling = false;

/**
 * Initialize Telegram bot
 */
async function initializeTelegramBot() {
  try {
    if (!BOT_TOKEN) {
      logger.warn('Telegram bot token not provided, Telegram notifications will be disabled');
      return null;
    }

    bot = new TelegramBot(BOT_TOKEN, { polling: false });

    // Set webhook if in production
    if (process.env.NODE_ENV === 'production' && WEBHOOK_URL) {
      await bot.setWebHook(WEBHOOK_URL, {
        secret_token: WEBHOOK_SECRET,
        allowed_updates: ['message', 'callback_query', 'my_chat_member']
      });
      logger.info('Telegram webhook set successfully');
    } else {
      // Use polling for development
      bot.startPolling();
      isPolling = true;
      logger.info('Telegram bot polling started');
    }

    // Set bot commands
    await setupBotCommands();

    // Setup message handlers
    setupMessageHandlers();

    logger.info('Telegram bot initialized successfully');
    return bot;

  } catch (error) {
    logger.error('Failed to initialize Telegram bot:', error);
    throw error;
  }
}

/**
 * Setup bot commands
 */
async function setupBotCommands() {
  try {
    const commands = [
      { command: 'start', description: 'Start using the AI Trading Platform bot' },
      { command: 'subscribe', description: 'Subscribe to trading notifications' },
      { command: 'unsubscribe', description: 'Unsubscribe from notifications' },
      { command: 'settings', description: 'Manage notification settings' },
      { command: 'status', description: 'Check subscription status' },
      { command: 'help', description: 'Show help information' }
    ];

    await bot.setMyCommands(commands);
    logger.info('Telegram bot commands set successfully');

  } catch (error) {
    logger.error('Error setting bot commands:', error);
  }
}

/**
 * Setup message handlers
 */
function setupMessageHandlers() {
  // Start command
  bot.onText(/\/start/, async (msg) => {
    const chatId = msg.chat.id;
    const firstName = msg.from.first_name;

    const welcomeMessage = `
🚀 Welcome to AI Trading Platform, ${firstName}!

I'm your personal trading assistant bot. I can send you:
• 📈 Trading signals and alerts
• 💰 Portfolio updates
• 📊 Market analysis
• ⚠️ Risk management notifications

To get started:
1. Link your account using /subscribe
2. Configure your notification preferences with /settings

Type /help for more commands.
    `;

    try {
      await bot.sendMessage(chatId, welcomeMessage, {
        reply_markup: {
          inline_keyboard: [
            [
              { text: '🔗 Link Account', callback_data: 'link_account' },
              { text: '⚙️ Settings', callback_data: 'settings' }
            ],
            [
              { text: '📖 Help', callback_data: 'help' }
            ]
          ]
        }
      });
    } catch (error) {
      logger.error('Error sending welcome message:', error);
    }
  });

  // Subscribe command
  bot.onText(/\/subscribe/, async (msg) => {
    const chatId = msg.chat.id;

    const subscribeMessage = `
🔗 Account Linking

To receive notifications, you need to link your AI Trading Platform account.

Please visit: ${process.env.FRONTEND_URL}/settings/notifications

And enter this Telegram Chat ID: \`${chatId}\`

Once linked, you'll start receiving personalized trading notifications!
    `;

    try {
      await bot.sendMessage(chatId, subscribeMessage, {
        parse_mode: 'Markdown',
        reply_markup: {
          inline_keyboard: [
            [
              { text: '🌐 Open Settings', url: `${process.env.FRONTEND_URL}/settings/notifications` }
            ]
          ]
        }
      });
    } catch (error) {
      logger.error('Error sending subscribe message:', error);
    }
  });

  // Unsubscribe command
  bot.onText(/\/unsubscribe/, async (msg) => {
    const chatId = msg.chat.id;

    try {
      // Find user by telegram chat ID and unsubscribe
      const result = await updateUserTelegramSettings(null, {
        telegramChatId: chatId,
        telegramEnabled: false
      });

      if (result) {
        await bot.sendMessage(chatId, '✅ You have been unsubscribed from notifications.');
      } else {
        await bot.sendMessage(chatId, '❌ No active subscription found for this chat.');
      }
    } catch (error) {
      logger.error('Error unsubscribing user:', error);
      await bot.sendMessage(chatId, '❌ Error unsubscribing. Please try again later.');
    }
  });

  // Settings command
  bot.onText(/\/settings/, async (msg) => {
    const chatId = msg.chat.id;

    try {
      const userSettings = await getUserTelegramSettings(chatId);

      if (!userSettings) {
        await bot.sendMessage(chatId, '❌ Account not linked. Use /subscribe to link your account.');
        return;
      }

      const settingsMessage = `
⚙️ **Notification Settings**

🔔 Notifications: ${userSettings.telegramEnabled ? '✅ Enabled' : '❌ Disabled'}
📈 Trading Signals: ${userSettings.tradingSignals ? '✅ On' : '❌ Off'}
💰 Portfolio Updates: ${userSettings.portfolioUpdates ? '✅ On' : '❌ Off'}
📊 Market Analysis: ${userSettings.marketAnalysis ? '✅ On' : '❌ Off'}
⚠️ Risk Alerts: ${userSettings.riskAlerts ? '✅ On' : '❌ Off'}

Subscription: ${userSettings.subscriptionTier}
      `;

      await bot.sendMessage(chatId, settingsMessage, {
        parse_mode: 'Markdown',
        reply_markup: {
          inline_keyboard: [
            [
              { text: userSettings.telegramEnabled ? '🔕 Disable' : '🔔 Enable', callback_data: 'toggle_notifications' }
            ],
            [
              { text: '📈 Signals', callback_data: 'toggle_signals' },
              { text: '💰 Portfolio', callback_data: 'toggle_portfolio' }
            ],
            [
              { text: '📊 Analysis', callback_data: 'toggle_analysis' },
              { text: '⚠️ Alerts', callback_data: 'toggle_alerts' }
            ],
            [
              { text: '🌐 Web Settings', url: `${process.env.FRONTEND_URL}/settings/notifications` }
            ]
          ]
        }
      });
    } catch (error) {
      logger.error('Error showing settings:', error);
      await bot.sendMessage(chatId, '❌ Error loading settings. Please try again later.');
    }
  });

  // Status command
  bot.onText(/\/status/, async (msg) => {
    const chatId = msg.chat.id;

    try {
      const userSettings = await getUserTelegramSettings(chatId);

      if (!userSettings) {
        await bot.sendMessage(chatId, '❌ Account not linked. Use /subscribe to link your account.');
        return;
      }

      const statusMessage = `
📊 **Account Status**

👤 User: ${userSettings.firstName} ${userSettings.lastName}
📧 Email: ${userSettings.email}
🎯 Subscription: ${userSettings.subscriptionTier}
🔔 Notifications: ${userSettings.telegramEnabled ? 'Active' : 'Disabled'}

📈 Recent Activity:
• Last notification: ${userSettings.lastNotification || 'None'}
• Total notifications sent: ${userSettings.notificationCount || 0}

For detailed account settings, visit: ${process.env.FRONTEND_URL}/dashboard
      `;

      await bot.sendMessage(chatId, statusMessage, {
        parse_mode: 'Markdown',
        reply_markup: {
          inline_keyboard: [
            [
              { text: '🌐 Open Dashboard', url: `${process.env.FRONTEND_URL}/dashboard` }
            ]
          ]
        }
      });
    } catch (error) {
      logger.error('Error showing status:', error);
      await bot.sendMessage(chatId, '❌ Error loading status. Please try again later.');
    }
  });

  // Help command
  bot.onText(/\/help/, async (msg) => {
    const chatId = msg.chat.id;

    const helpMessage = `
🤖 **AI Trading Platform Bot Help**

**Commands:**
/start - Start using the bot
/subscribe - Link your account for notifications
/unsubscribe - Stop receiving notifications
/settings - Configure notification preferences
/status - Check your account status
/help - Show this help message

**Features:**
• 📈 Real-time trading signals
• 💰 Portfolio performance updates
• 📊 Market analysis and insights
• ⚠️ Risk management alerts
• 🎯 Personalized notifications based on your subscription

**Need Help?**
Visit our support center: ${process.env.SUPPORT_URL || 'https://help.aitrading.app'}
Or contact us at: support@aitrading.app
    `;

    try {
      await bot.sendMessage(chatId, helpMessage, {
        parse_mode: 'Markdown',
        reply_markup: {
          inline_keyboard: [
            [
              { text: '🌐 Visit Website', url: process.env.FRONTEND_URL || 'https://aitrading.app' },
              { text: '📞 Support', url: process.env.SUPPORT_URL || 'https://help.aitrading.app' }
            ]
          ]
        }
      });
    } catch (error) {
      logger.error('Error sending help message:', error);
    }
  });

  // Handle callback queries (inline button presses)
  bot.on('callback_query', async (callbackQuery) => {
    const message = callbackQuery.message;
    const data = callbackQuery.data;
    const chatId = message.chat.id;

    try {
      await handleCallbackQuery(chatId, data, callbackQuery.id);
    } catch (error) {
      logger.error('Error handling callback query:', error);
      await bot.answerCallbackQuery(callbackQuery.id, { text: 'Error processing request' });
    }
  });
}

/**
 * Handle callback queries from inline keyboards
 */
async function handleCallbackQuery(chatId, data, callbackQueryId) {
  switch (data) {
    case 'link_account':
      await bot.answerCallbackQuery(callbackQueryId, { text: 'Opening account linking...' });
      await bot.sendMessage(chatId, `🔗 Link your account at: ${process.env.FRONTEND_URL}/settings/notifications\n\nYour Chat ID: \`${chatId}\``, {
        parse_mode: 'Markdown'
      });
      break;

    case 'settings':
      await bot.answerCallbackQuery(callbackQueryId, { text: 'Loading settings...' });
      // Trigger settings command
      await bot.sendMessage(chatId, '/settings');
      break;

    case 'help':
      await bot.answerCallbackQuery(callbackQueryId, { text: 'Opening help...' });
      // Trigger help command
      await bot.sendMessage(chatId, '/help');
      break;

    case 'toggle_notifications':
    case 'toggle_signals':
    case 'toggle_portfolio':
    case 'toggle_analysis':
    case 'toggle_alerts':
      await handleSettingsToggle(chatId, data, callbackQueryId);
      break;

    default:
      await bot.answerCallbackQuery(callbackQueryId, { text: 'Unknown action' });
  }
}

/**
 * Handle settings toggle callbacks
 */
async function handleSettingsToggle(chatId, action, callbackQueryId) {
  try {
    const userSettings = await getUserTelegramSettings(chatId);

    if (!userSettings) {
      await bot.answerCallbackQuery(callbackQueryId, { text: 'Account not linked' });
      return;
    }

    let updateData = {};
    let message = '';

    switch (action) {
      case 'toggle_notifications':
        updateData.telegramEnabled = !userSettings.telegramEnabled;
        message = `Notifications ${updateData.telegramEnabled ? 'enabled' : 'disabled'}`;
        break;
      case 'toggle_signals':
        updateData.tradingSignals = !userSettings.tradingSignals;
        message = `Trading signals ${updateData.tradingSignals ? 'enabled' : 'disabled'}`;
        break;
      case 'toggle_portfolio':
        updateData.portfolioUpdates = !userSettings.portfolioUpdates;
        message = `Portfolio updates ${updateData.portfolioUpdates ? 'enabled' : 'disabled'}`;
        break;
      case 'toggle_analysis':
        updateData.marketAnalysis = !userSettings.marketAnalysis;
        message = `Market analysis ${updateData.marketAnalysis ? 'enabled' : 'disabled'}`;
        break;
      case 'toggle_alerts':
        updateData.riskAlerts = !userSettings.riskAlerts;
        message = `Risk alerts ${updateData.riskAlerts ? 'enabled' : 'disabled'}`;
        break;
    }

    await updateUserTelegramSettings(userSettings.userId, updateData);
    await bot.answerCallbackQuery(callbackQueryId, { text: message });

    // Refresh settings display
    setTimeout(() => {
      bot.sendMessage(chatId, '/settings');
    }, 1000);

  } catch (error) {
    logger.error('Error toggling settings:', error);
    await bot.answerCallbackQuery(callbackQueryId, { text: 'Error updating settings' });
  }
}

/**
 * Send notification via Telegram
 */
async function sendTelegramNotification(chatId, notification) {
  try {
    if (!bot) {
      throw new Error('Telegram bot not initialized');
    }

    const { title, message, type, data } = notification;

    // Format message based on type
    let formattedMessage = `*${title}*\n\n${message}`;

    // Add type-specific formatting and emojis
    switch (type) {
      case 'trading_signal':
        formattedMessage = `🚨 *Trading Signal*\n\n${message}`;
        break;
      case 'portfolio_update':
        formattedMessage = `💰 *Portfolio Update*\n\n${message}`;
        break;
      case 'market_analysis':
        formattedMessage = `📊 *Market Analysis*\n\n${message}`;
        break;
      case 'risk_alert':
        formattedMessage = `⚠️ *Risk Alert*\n\n${message}`;
        break;
      case 'system_notification':
        formattedMessage = `🔔 *System Notification*\n\n${message}`;
        break;
      default:
        formattedMessage = `📢 *${title}*\n\n${message}`;
    }

    // Add timestamp
    formattedMessage += `\n\n🕐 ${new Date().toLocaleString('en-US', { timeZone: 'Asia/Jakarta' })} WIB`;

    // Send message
    const sentMessage = await bot.sendMessage(chatId, formattedMessage, {
      parse_mode: 'Markdown',
      disable_web_page_preview: true
    });

    logger.info(`Telegram notification sent to chat ${chatId}`);
    return sentMessage;

  } catch (error) {
    logger.error('Error sending Telegram notification:', error);
    throw error;
  }
}

/**
 * Process webhook update
 */
async function processWebhookUpdate(update) {
  try {
    if (update.message) {
      // Regular message - process with handlers
      await bot.processUpdate(update);
    } else if (update.callback_query) {
      // Callback query - process with handlers
      await bot.processUpdate(update);
    } else if (update.my_chat_member) {
      // Bot was added/removed from chat
      logger.info('Bot chat member status changed:', update.my_chat_member);
    }

    return { success: true };

  } catch (error) {
    logger.error('Error processing webhook update:', error);
    throw error;
  }
}

/**
 * Get bot info
 */
async function getBotInfo() {
  try {
    if (!bot) {
      return { status: 'disabled', message: 'Bot not initialized' };
    }

    const me = await bot.getMe();
    return {
      status: 'active',
      botInfo: {
        id: me.id,
        username: me.username,
        firstName: me.first_name,
        canJoinGroups: me.can_join_groups,
        canReadAllGroupMessages: me.can_read_all_group_messages,
        supportsInlineQueries: me.supports_inline_queries
      },
      webhookInfo: await getWebhookInfo()
    };

  } catch (error) {
    logger.error('Error getting bot info:', error);
    throw error;
  }
}

/**
 * Get webhook info
 */
async function getWebhookInfo() {
  try {
    if (!bot) {
      return null;
    }

    return await bot.getWebHookInfo();
  } catch (error) {
    logger.error('Error getting webhook info:', error);
    return null;
  }
}

module.exports = {
  initializeTelegramBot,
  sendTelegramNotification,
  processWebhookUpdate,
  getBotInfo,
  getWebhookInfo
};