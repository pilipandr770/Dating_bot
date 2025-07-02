# файл: app/handlers/tokens.py

from aiogram import types, Dispatcher
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from app.services.token_service import get_user_balance, update_user_balance, transfer_tokens, request_withdrawal
from app.services.user_service import get_user_by_telegram_id, get_user_language
from app.keyboards.main_menu import get_main_menu
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

# Состояния для операций с токенами
class TokenStates(StatesGroup):
    waiting_for_transfer_amount = State()  # Ввод суммы для перевода
    waiting_for_receiver_id = State()      # Ввод ID получателя
    waiting_for_withdrawal_amount = State() # Ввод суммы для вывода

# Обработчик команды /balance - показать текущий баланс
async def cmd_balance(message: types.Message):
    telegram_id = str(message.from_user.id)
    balance = await get_user_balance(telegram_id)
    
    # Получаем язык пользователя
    lang = await get_user_language(telegram_id)
    
    # Локализованные сообщения
    texts = {
        "ua": f"💰 Ваш поточний баланс: {balance} токенів",
        "ru": f"💰 Ваш текущий баланс: {balance} токенов",
        "en": f"💰 Your current balance: {balance} tokens",
        "de": f"💰 Ihr aktuelles Guthaben: {balance} Token"
    }
    
    # Создаем инлайн клавиатуру для операций с токенами
    markup = InlineKeyboardMarkup(row_width=2)
    
    # Локализованные кнопки
    button_texts = {
        "ua": {"add": "➕ Поповнити", "transfer": "🔄 Переказати", "withdraw": "💸 Вивести"},
        "ru": {"add": "➕ Пополнить", "transfer": "🔄 Перевести", "withdraw": "💸 Вывести"},
        "en": {"add": "➕ Add tokens", "transfer": "🔄 Transfer", "withdraw": "💸 Withdraw"},
        "de": {"add": "➕ Aufladen", "transfer": "🔄 Überweisen", "withdraw": "💸 Abheben"}
    }
    
    t = button_texts.get(lang, button_texts["en"])
    
    markup.add(
        InlineKeyboardButton(t["add"], callback_data="token_add"),
        InlineKeyboardButton(t["transfer"], callback_data="token_transfer")
    )
    markup.add(InlineKeyboardButton(t["withdraw"], callback_data="token_withdraw"))
    
    await message.answer(texts.get(lang, texts["en"]), reply_markup=markup)

# Обработчик для пополнения баланса
async def on_token_add(callback_query: types.CallbackQuery):
    # Получаем язык пользователя
    lang = await get_user_language(str(callback_query.from_user.id))
    
    # Локализованные сообщения
    texts = {
        "ua": "Оберіть пакет токенів для покупки:",
        "ru": "Выберите пакет токенов для покупки:",
        "en": "Choose a token package to purchase:",
        "de": "Wählen Sie ein Token-Paket zum Kauf:"
    }
    
    # Создаем инлайн клавиатуру с пакетами токенов
    markup = InlineKeyboardMarkup(row_width=2)
    
    # Пакеты токенов: название, цена в EUR, количество токенов
    token_packages = [
        {"name": "100 tokens", "price": 10, "tokens": 100},
        {"name": "200 tokens", "price": 18, "tokens": 200},
        {"name": "500 tokens", "price": 40, "tokens": 500},
        {"name": "1000 tokens", "price": 75, "tokens": 1000}
    ]
    
    for package in token_packages:
        button_text = f"{package['name']} - {package['price']}€"
        markup.add(InlineKeyboardButton(button_text, callback_data=f"buy_tokens_{package['tokens']}"))
    
    # Кнопка отмены
    cancel_texts = {
        "ua": "❌ Скасувати",
        "ru": "❌ Отменить",
        "en": "❌ Cancel",
        "de": "❌ Abbrechen"
    }
    markup.add(InlineKeyboardButton(cancel_texts.get(lang, cancel_texts["en"]), callback_data="cancel_token_operation"))
    
    await callback_query.message.edit_text(texts.get(lang, texts["en"]), reply_markup=markup)
    await callback_query.answer()

# Обработчик для покупки выбранного пакета токенов
async def on_buy_tokens(callback_query: types.CallbackQuery):
    token_amount = int(callback_query.data.split('_')[2])
    telegram_id = str(callback_query.from_user.id)
    
    # Получаем язык пользователя
    lang = await get_user_language(telegram_id)
    
    # Здесь должно быть перенаправление на страницу оплаты Stripe
    from app.services.stripe import create_checkout_session
    from app.database import get_session
    
    user = await get_user_by_telegram_id(telegram_id)
    
    if not user:
        return await callback_query.answer("❌ User not found", show_alert=True)
    
    async for session in get_session():
        try:
            # Создаем сессию оплаты Stripe для покупки токенов
            checkout_url = await create_checkout_session(user.id, "tokens", session)
            
            # Отправляем пользователю ссылку на оплату
            # Локализованные сообщения
            texts = {
                "ua": f"Для покупки {token_amount} токенів перейдіть за посиланням:",
                "ru": f"Для покупки {token_amount} токенов перейдите по ссылке:",
                "en": f"To purchase {token_amount} tokens, follow the link:",
                "de": f"Um {token_amount} Token zu kaufen, folgen Sie dem Link:"
            }
            
            markup = InlineKeyboardMarkup()
            
            button_texts = {
                "ua": "💳 Перейти до оплати",
                "ru": "💳 Перейти к оплате",
                "en": "💳 Go to payment",
                "de": "💳 Zur Zahlung gehen"
            }
            
            markup.add(InlineKeyboardButton(
                button_texts.get(lang, button_texts["en"]), 
                url=checkout_url
            ))
            
            await callback_query.message.edit_text(
                texts.get(lang, texts["en"]),
                reply_markup=markup
            )
            await callback_query.answer()
        
        except Exception as e:
            error_texts = {
                "ua": "❌ Помилка при створенні платежу. Спробуйте пізніше.",
                "ru": "❌ Ошибка при создании платежа. Попробуйте позже.",
                "en": "❌ Error creating payment. Please try again later.",
                "de": "❌ Fehler beim Erstellen der Zahlung. Bitte versuchen Sie es später erneut."
            }
            await callback_query.message.edit_text(error_texts.get(lang, error_texts["en"]))
            await callback_query.answer()
            print(f"Payment creation error: {str(e)}")

# Обработчик для перевода токенов
async def on_token_transfer(callback_query: types.CallbackQuery, state: FSMContext):
    # Получаем язык пользователя
    lang = await get_user_language(str(callback_query.from_user.id))
    
    # Локализованные сообщения
    texts = {
        "ua": "Введіть ID користувача, якому хочете переказати токени:\n(Це число в їх профілі)",
        "ru": "Введите ID пользователя, которому хотите перевести токены:\n(Это число в их профиле)",
        "en": "Enter the user ID to transfer tokens to:\n(This is the number in their profile)",
        "de": "Geben Sie die Benutzer-ID ein, an die Sie Token überweisen möchten:\n(Dies ist die Nummer in ihrem Profil)"
    }
    
    await callback_query.message.edit_text(texts.get(lang, texts["en"]))
    
    # Устанавливаем состояние ожидания ID получателя
    await TokenStates.waiting_for_receiver_id.set()
    await callback_query.answer()

# Обработчик для получения ID получателя токенов
async def process_receiver_id(message: types.Message, state: FSMContext):
    try:
        receiver_id = message.text.strip()
        
        # Проверяем, что ID получателя - число
        if not receiver_id.isdigit():
            raise ValueError("ID должен быть числом")
            
        # Сохраняем ID получателя в состоянии
        await state.update_data(receiver_id=receiver_id)
        
        # Получаем язык пользователя
        lang = await get_user_language(str(message.from_user.id))
        
        # Локализованные сообщения
        texts = {
            "ua": "Введіть кількість токенів для переказу:",
            "ru": "Введите количество токенов для перевода:",
            "en": "Enter the number of tokens to transfer:",
            "de": "Geben Sie die Anzahl der zu überweisenden Token ein:"
        }
        
        await message.answer(texts.get(lang, texts["en"]))
        
        # Устанавливаем состояние ожидания суммы перевода
        await TokenStates.waiting_for_transfer_amount.set()
    except Exception as e:
        # Получаем язык пользователя
        lang = await get_user_language(str(message.from_user.id))
        
        # Локализованные сообщения об ошибке
        error_texts = {
            "ua": "❌ Невірний формат ID. Спробуйте ще раз.",
            "ru": "❌ Неверный формат ID. Попробуйте еще раз.",
            "en": "❌ Invalid ID format. Please try again.",
            "de": "❌ Ungültiges ID-Format. Bitte versuchen Sie es erneut."
        }
        
        await message.answer(error_texts.get(lang, error_texts["en"]))

# Обработчик для получения суммы перевода
async def process_transfer_amount(message: types.Message, state: FSMContext):
    try:
        amount = int(message.text.strip())
        
        if amount <= 0:
            raise ValueError("Amount must be positive")
        
        # Получаем данные из состояния
        data = await state.get_data()
        receiver_id = data.get("receiver_id")
        
        # Выполняем перевод токенов
        sender_id = str(message.from_user.id)
        success = await transfer_tokens(sender_id, receiver_id, amount)
        
        # Получаем язык пользователя
        lang = await get_user_language(sender_id)
        
        if success:
            # Локализованные сообщения об успехе
            success_texts = {
                "ua": f"✅ Ви успішно перевели {amount} токенів користувачу з ID {receiver_id}.",
                "ru": f"✅ Вы успешно перевели {amount} токенов пользователю с ID {receiver_id}.",
                "en": f"✅ You have successfully transferred {amount} tokens to user with ID {receiver_id}.",
                "de": f"✅ Sie haben erfolgreich {amount} Token an den Benutzer mit der ID {receiver_id} überwiesen."
            }
            
            await message.answer(success_texts.get(lang, success_texts["en"]), reply_markup=get_main_menu(lang))
        else:
            # Локализованные сообщения об ошибке
            error_texts = {
                "ua": "❌ Не вдалося виконати переказ. Перевірте баланс та правильність ID отримувача.",
                "ru": "❌ Не удалось выполнить перевод. Проверьте баланс и правильность ID получателя.",
                "en": "❌ Transfer failed. Check your balance and the recipient's ID.",
                "de": "❌ Überweisung fehlgeschlagen. Überprüfen Sie Ihr Guthaben und die ID des Empfängers."
            }
            
            await message.answer(error_texts.get(lang, error_texts["en"]), reply_markup=get_main_menu(lang))
        
        # Сбрасываем состояние
        await state.finish()
    except ValueError:
        # Получаем язык пользователя
        lang = await get_user_language(str(message.from_user.id))
        
        # Локализованные сообщения об ошибке
        error_texts = {
            "ua": "❌ Невірний формат суми. Введіть ціле число більше 0.",
            "ru": "❌ Неверный формат суммы. Введите целое число больше 0.",
            "en": "❌ Invalid amount format. Enter an integer greater than 0.",
            "de": "❌ Ungültiges Summenformat. Geben Sie eine ganze Zahl größer als 0 ein."
        }
        
        await message.answer(error_texts.get(lang, error_texts["en"]))

# Обработчик для вывода токенов
async def on_token_withdraw(callback_query: types.CallbackQuery, state: FSMContext):
    # Получаем язык пользователя
    lang = await get_user_language(str(callback_query.from_user.id))
    
    # Локализованные сообщения
    texts = {
        "ua": "Введіть кількість токенів для виведення:",
        "ru": "Введите количество токенов для вывода:",
        "en": "Enter the number of tokens to withdraw:",
        "de": "Geben Sie die Anzahl der Token ein, die Sie abheben möchten:"
    }
    
    await callback_query.message.edit_text(texts.get(lang, texts["en"]))
    
    # Устанавливаем состояние ожидания суммы вывода
    await TokenStates.waiting_for_withdrawal_amount.set()
    await callback_query.answer()

# Обработчик для получения суммы вывода
async def process_withdrawal_amount(message: types.Message, state: FSMContext):
    try:
        amount = int(message.text.strip())
        
        if amount <= 0:
            raise ValueError("Amount must be positive")
        
        # Выполняем запрос на вывод токенов
        telegram_id = str(message.from_user.id)
        success = await request_withdrawal(telegram_id, amount)
        
        # Получаем язык пользователя
        lang = await get_user_language(telegram_id)
        
        if success:
            # Локализованные сообщения об успехе
            success_texts = {
                "ua": f"✅ Ваш запит на виведення {amount} токенів успішно створено. Очікуйте на обробку адміністратором.",
                "ru": f"✅ Ваш запрос на вывод {amount} токенов успешно создан. Ожидайте обработки администратором.",
                "en": f"✅ Your request to withdraw {amount} tokens has been successfully created. Wait for processing by the administrator.",
                "de": f"✅ Ihre Anfrage zum Abheben von {amount} Token wurde erfolgreich erstellt. Warten Sie auf die Bearbeitung durch den Administrator."
            }
            
            await message.answer(success_texts.get(lang, success_texts["en"]), reply_markup=get_main_menu(lang))
        else:
            # Локализованные сообщения об ошибке
            error_texts = {
                "ua": "❌ Не вдалося створити запит на виведення. Перевірте баланс.",
                "ru": "❌ Не удалось создать запрос на вывод. Проверьте баланс.",
                "en": "❌ Failed to create withdrawal request. Check your balance.",
                "de": "❌ Die Auszahlungsanforderung konnte nicht erstellt werden. Überprüfen Sie Ihr Guthaben."
            }
            
            await message.answer(error_texts.get(lang, error_texts["en"]), reply_markup=get_main_menu(lang))
        
        # Сбрасываем состояние
        await state.finish()
    except ValueError:
        # Получаем язык пользователя
        lang = await get_user_language(str(message.from_user.id))
        
        # Локализованные сообщения об ошибке
        error_texts = {
            "ua": "❌ Невірний формат суми. Введіть ціле число більше 0.",
            "ru": "❌ Неверный формат суммы. Введите целое число больше 0.",
            "en": "❌ Invalid amount format. Enter an integer greater than 0.",
            "de": "❌ Ungültiges Summenformat. Geben Sie eine ganze Zahl größer als 0 ein."
        }
        
        await message.answer(error_texts.get(lang, error_texts["en"]))

# Обработчик отмены операций с токенами
async def on_cancel_token_operation(callback_query: types.CallbackQuery, state: FSMContext):
    # Получаем язык пользователя
    lang = await get_user_language(str(callback_query.from_user.id))
    
    # Локализованные сообщения
    texts = {
        "ua": "❌ Операцію скасовано.",
        "ru": "❌ Операция отменена.",
        "en": "❌ Operation canceled.",
        "de": "❌ Vorgang abgebrochen."
    }
    
    await callback_query.message.edit_text(texts.get(lang, texts["en"]))
    
    # Сбрасываем состояние
    await state.finish()
    await callback_query.answer()

# Регистрация обработчиков
def register_token_handlers(dp: Dispatcher):
    # Команда для просмотра баланса
    dp.register_message_handler(cmd_balance, commands="balance", state="*")
    
    # Текстовая кнопка для просмотра баланса
    dp.register_message_handler(
        cmd_balance,
        lambda m: any(token in m.text.lower() for token in ["баланс", "balance", "guthaben", "токени", "токены", "tokens"]),
        state="*"
    )
    
    # Обработчики инлайн-кнопок
    dp.register_callback_query_handler(on_token_add, lambda c: c.data == "token_add", state="*")
    dp.register_callback_query_handler(on_token_transfer, lambda c: c.data == "token_transfer", state="*")
    dp.register_callback_query_handler(on_token_withdraw, lambda c: c.data == "token_withdraw", state="*")
    dp.register_callback_query_handler(on_buy_tokens, lambda c: c.data.startswith("buy_tokens_"), state="*")
    dp.register_callback_query_handler(on_cancel_token_operation, lambda c: c.data == "cancel_token_operation", state="*")
    
    # Обработчики состояний для переводов
    dp.register_message_handler(process_receiver_id, state=TokenStates.waiting_for_receiver_id)
    dp.register_message_handler(process_transfer_amount, state=TokenStates.waiting_for_transfer_amount)
    dp.register_message_handler(process_withdrawal_amount, state=TokenStates.waiting_for_withdrawal_amount)
