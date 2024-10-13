import requests
from bs4 import BeautifulSoup
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CommandHandler, CallbackQueryHandler, MessageHandler, filters, ConversationHandler, CallbackContext, ApplicationBuilder

# تعريف الحالات للمحادثة
CHOOSING_BRANCH, TYPING_ID = range(2)

# توكن البوت
TOKEN = '7579569551:AAGRPKqXaCyZ44O5XAl51Uab9O44vAzvFCA'  # توكن البوت الخاص بك

# URL الخاص بالصفحة
url = 'https://exam.albaath-univ.edu.sy/exam-petro/'

async def start(update: Update, context: CallbackContext) -> int:
    response = requests.get(url)
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')
        branch_select = soup.find('select', {'name': 'nospy'})
        branches = [(option.text, option['value']) for option in branch_select.find_all('option') if option['value'] in ['1', '3']]  # فقط البترول والغذائية

        keyboard = [[InlineKeyboardButton(branch[0], callback_data=branch[1]) for branch in branches]]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.message.reply_text('اختر الفرع:', reply_markup=reply_markup)
        return CHOOSING_BRANCH
    else:
        await update.message.reply_text('خطأ في الاتصال بالخادم: {}'.format(response.status_code))
        return ConversationHandler.END

async def choose_branch(update: Update, context: CallbackContext) -> int:
    query = update.callback_query
    await query.answer()

    context.user_data['branch_code'] = query.data
    await query.edit_message_text(text="الرجاء إدخال رقمك الجامعي:")
    return TYPING_ID

async def receive_student_id(update: Update, context: CallbackContext) -> int:
    student_id = update.message.text.strip()
    branch_code = context.user_data.get('branch_code')

    data = {
        'number1': student_id,
        'nospy': branch_code
    }

    response = requests.post('https://exam.albaath-univ.edu.sy/exam-petro/re.php', data=data)

    if response.status_code == 200:
        results_soup = BeautifulSoup(response.text, 'html.parser')

        # استخراج اسم الطالب
        name = results_soup.find('td', colspan="4").text.strip() if results_soup.find('td', colspan="4") else "اسم الطالب غير موجود"

        # إعداد الرسالة لاسم الطالب
        name_message = f'اسم الطالب: {name}\n\n'

        # استخراج الدرجات
        subjects = results_soup.find_all('tr')[2:]  # تخطي الصفين الأولين
        results = []

        for index, subject in enumerate(subjects, start=1):
            cells = subject.find_all('td')
            if len(cells) >= 4:
                subject_name = cells[0].text.strip()
                practical_score = cells[1].text.strip() or "0"
                theoretical_score = cells[2].text.strip() or "0"
                final_score = cells[3].text.strip() or "0"

                # التحقق من النجاح أو الرسوب
                result_status = "😍 ناجح" if int(final_score) >= 60 else "☹️ راسب"

                results.append(f'المادة {index}:\nالمادة: {subject_name}\nدرجة العملي: {practical_score}\nدرجة النظري: {theoretical_score}\nالدرجة النهائية: {final_score}\nالحالة: {result_status}\n')

        results_message = name_message + '\n'.join(results)  # إضافة مسافات

        await update.message.reply_text(results_message)

        # هنا يمكنك إضافة الفقاعات أو الرسوم المتحركة عند ظهور النتائج
        if "😍 ناجح" in results_message:
            await update.message.reply_text("🎉 مبروك! لديك نتائج رائعة! 🎉")

    else:
        await update.message.reply_text(f'حدث خطأ أثناء إرسال البيانات: {response.status_code}')
        print('محتوى الاستجابة:', response.text)

    return ConversationHandler.END

async def cancel(update: Update, context: CallbackContext) -> int:
    await update.message.reply_text('تم إنهاء المحادثة.')
    return ConversationHandler.END

def main():
    application = ApplicationBuilder().token(TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            CHOOSING_BRANCH: [CallbackQueryHandler(choose_branch)],
            TYPING_ID: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_student_id)],
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    )

    application.add_handler(conv_handler)

    application.run_polling()

if __name__ == '__main__':
    main()
