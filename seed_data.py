import os
import django
from django.utils import timezone
from datetime import timedelta
import uuid

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Config.settings')
django.setup()

from django.contrib.auth import get_user_model
from django.db import transaction
from language_academy.models import (
    World, Chapter, Lesson, LessonContent, Quiz,
    Question, QuestionChoice, Exam, ExamQuestion,
    VocabularyCategory, Vocabulary, VocabularyExample,
    Badge, DailyGoal, Dialogue, DialogueScene, DialogueChoice,
    UserLessonProgress, UserChapterProgress, UserWorldProgress,
    UserVocabularyProgress, Certificate, CoinTransaction,
    LearningAnalytics
)

User = get_user_model()


GRAMMAR_DATA = {

    "Airport Vocabulary": {
        "notes": """
        <h4>📖 Present Simple Tense - Verb "TO BE"</h4>
        <p><strong>Positive:</strong></p>
        <ul>
            <li>I <strong>am</strong> a passenger.</li>
            <li>You <strong>are</strong> at the airport.</li>
            <li>He/She/It <strong>is</strong> in the terminal.</li>
            <li>We/They <strong>are</strong> at the gate.</li>
        </ul>
        <p><strong>Negative:</strong></p>
        <ul>
            <li>I <strong>am not</strong> late.</li>
            <li>You <strong>are not</strong> at the wrong gate.</li>
            <li>She <strong>is not</strong> in the terminal.</li>
        </ul>
        <p><strong>Questions:</strong></p>
        <ul>
            <li><strong>Am</strong> I at the right gate?</li>
            <li><strong>Are</strong> you ready to board?</li>
            <li><strong>Is</strong> this your flight?</li>
        </ul>
        """,
        "examples": [
            "I am a passenger on flight 2025.",
            "The gate is at the end of the terminal.",
            "We are waiting for the boarding announcement."
        ]
    },
    "Checking In": {
        "notes": """
        <h4>📝 Asking Questions with "Can" and "May"</h4>
        <p><strong>Asking for permission:</strong></p>
        <ul>
            <li>"May I see your passport?"</li>
            <li>"Can I have your ticket?"</li>
            <li>"Could I ask you some questions?"</li>
        </ul>
        <p><strong>Offering help:</strong></p>
        <ul>
            <li>"Can I help you with your luggage?"</li>
            <li>"May I assist you?"</li>
        </ul>
        <p><strong>Making requests:</strong></p>
        <ul>
            <li>"Can you open your bag, please?"</li>
            <li>"Could you show me your ID?"</li>
        </ul>
        """,
        "examples": [
            "Agent: May I see your passport and ticket?",
            "Passenger: Yes, here you are.",
            "Agent: Do you have any luggage to check?"
        ]
    },
    "Security & Boarding": {
        "notes": """
        <h4>📖 Imperatives - Giving Instructions</h4>
        <p><strong>Positive instructions:</strong></p>
        <ul>
            <li>"Put your bag on the belt."</li>
            <li>"Take off your jacket."</li>
            <li>"Take your electronics out of your bag."</li>
            <li>"Walk through the detector."</li>
        </ul>
        <p><strong>Negative instructions:</strong></p>
        <ul>
            <li>"Don't forget your belongings."</li>
            <li>"Don't take pictures in security."</li>
            <li>"Don't leave anything behind."</li>
        </ul>
        """,
        "examples": [
            "Security Officer: Please put your bag on the belt.",
            "Security Officer: Take your electronics out.",
            "Announcer: Please proceed to your gate."
        ]
    },
    "Arrivals & Baggage": {
        "notes": """
        <h4>📖 Past Simple - Regular Verbs</h4>
        <p><strong>Positive:</strong></p>
        <ul>
            <li>I <strong>arrived</strong> at the airport.</li>
            <li>You <strong>waited</strong> for your bag.</li>
            <li>We <strong>walked</strong> through customs.</li>
        </ul>
        <p><strong>Negative:</strong></p>
        <ul>
            <li>I <strong>did not (didn't)</strong> see my bag.</li>
            <li>You <strong>did not (didn't)</strong> wait long.</li>
        </ul>
        <p><strong>Question:</strong></p>
        <ul>
            <li><strong>Did</strong> you find your bag?</li>
            <li><strong>Did</strong> you go through customs?</li>
        </ul>
        """,
        "examples": [
            "I arrived at the airport and went to baggage claim.",
            "I waited for my bag on the carousel.",
            "After customs, I left the airport."
        ]
    },
    "In-Flight Experience": {
        "notes": """
        <h4>✈️ Present Continuous - Actions in Progress</h4>
        <p><strong>Positive:</strong></p>
        <ul>
            <li>I <strong>am sitting</strong> in seat 22A.</li>
            <li>You <strong>are reading</strong> a magazine.</li>
            <li>He <strong>is sleeping</strong> next to me.</li>
        </ul>
        <p><strong>Negative:</strong></p>
        <ul>
            <li>I <strong>am not sleeping</strong>.</li>
            <li>They <strong>are not eating</strong> right now.</li>
        </ul>
        """,
        "examples": [
            "The flight attendant is serving drinks.",
            "I am watching a movie on the screen.",
            "She is looking out the window."
        ]
    },
    "Flight Delays": {
        "notes": """
        <h4>⏰ Future with "Going to"</h4>
        <p><strong>Plans and predictions:</strong></p>
        <ul>
            <li>"The flight <strong>is going to</strong> be delayed."</li>
            <li>"We <strong>are going to</strong> wait for 2 hours."</li>
            <li>"I <strong>am going to</strong> call my family."</li>
        </ul>
        <p><strong>Negative:</strong></p>
        <ul>
            <li>"It <strong>is not going to</strong> be a short flight."</li>
        </ul>
        """,
        "examples": [
            "The announcement says the flight is going to be delayed.",
            "We are going to wait at the gate.",
            "I am going to buy some food."
        ]
    },


    "Menu & Ordering": {
        "notes": """
        <h4>🍽️ Ordering Food - "I would like..."</h4>
        <p><strong>Making an order:</strong></p>
        <ul>
            <li>"I <strong>would like</strong> the grilled salmon."</li>
            <li>"I <strong>would like</strong> a glass of water."</li>
            <li>"I <strong>would like</strong> to see the menu."</li>
        </ul>
        <p><strong>Short form:</strong></p>
        <ul>
            <li>"I <strong>would like</strong>..." → "I'd like..."</li>
            <li>"I would like the pasta." → "I'd like the pasta."</li>
        </ul>
        """,
        "examples": [
            "I would like to order the grilled salmon with vegetables.",
            "I would like a glass of white wine, please.",
            "I would like the menu, please."
        ]
    },
    "Table Conversation": {
        "notes": """
        <h4>💬 Polite Requests and Offers</h4>
        <p><strong>Making polite requests:</strong></p>
        <ul>
            <li>"<strong>Could</strong> I have the salt, please?"</li>
            <li>"<strong>Would</strong> you pass the bread?"</li>
            <li>"<strong>Can</strong> I have some more water?"</li>
        </ul>
        <p><strong>Making offers:</strong></p>
        <ul>
            <li>"<strong>Would</strong> you like some dessert?"</li>
            <li>"<strong>Can</strong> I get you anything else?"</li>
        </ul>
        """,
        "examples": [
            "Could I have the bill, please?",
            "Would you like to see the dessert menu?",
            "Can I get you another drink?"
        ]
    },
    "Paying the Bill": {
        "notes": """
        <h4>💰 Asking About Payment</h4>
        <p><strong>Asking about payment methods:</strong></p>
        <ul>
            <li>"Do you accept credit cards?"</li>
            <li>"Can I pay with cash?"</li>
            <li>"Is service charge included?"</li>
        </ul>
        <p><strong>At the checkout:</strong></p>
        <ul>
            <li>"Could we have the bill, please?"</li>
            <li>"I'd like to pay now."</li>
            <li>"Keep the change."</li>
        </ul>
        """,
        "examples": [
            "Customer: Could we have the bill, please?",
            "Waiter: Certainly. Here you are.",
            "Customer: Keep the change."
        ]
    },
    "Food & Culture": {
        "notes": """
        <h4>🌍 Comparing Cultures - Comparative Adjectives</h4>
        <p><strong>Comparatives:</strong></p>
        <ul>
            <li>"Italian food is <strong>more popular</strong> than British food."</li>
            <li>"Chopsticks are <strong>more common</strong> in Asia."</li>
            <li>"Spicy food is <strong>hotter</strong> than mild food."</li>
        </ul>
        <p><strong>Superlatives:</strong></p>
        <ul>
            <li>"Pizza is the <strong>most popular</strong> food in Italy."</li>
            <li>"Sushi is the <strong>healthiest</strong> option."</li>
        </ul>
        """,
        "examples": [
            "Italian food is more popular than British food.",
            "Chopsticks are more common in Asia.",
            "Pizza is the most popular food in Italy."
        ]
    },
    "Cooking at Home": {
        "notes": """
        <h4>👨‍🍳 Cooking Instructions - Sequence Words</h4>
        <p><strong>Sequence words:</strong></p>
        <ul>
            <li><strong>First</strong>, chop the onions.</li>
            <li><strong>Then</strong>, add the garlic.</li>
            <li><strong>Next</strong>, pour in the tomato sauce.</li>
            <li><strong>Finally</strong>, serve with pasta.</li>
        </ul>
        """,
        "examples": [
            "First, chop the onions and garlic.",
            "Then, add the tomatoes and spices.",
            "Finally, serve with fresh pasta."
        ]
    },
    "Restaurant Review": {
        "notes": """
        <h4>⭐ Expressing Opinions</h4>
        <p><strong>Giving opinions:</strong></p>
        <ul>
            <li>"I <strong>think</strong> the food was amazing."</li>
            <li>"<strong>In my opinion</strong>, it was too expensive."</li>
            <li>"I <strong>believe</strong> this is the best restaurant."</li>
        </ul>
        <p><strong>Agreeing/Disagreeing:</strong></p>
        <ul>
            <li>"I <strong>agree</strong> with you."</li>
            <li>"I <strong>disagree</strong>. The service was slow."</li>
        </ul>
        """,
        "examples": [
            "In my opinion, this is the best restaurant in town.",
            "I think the food was delicious.",
            "I agree with you. The service was excellent."
        ]
    },


    "Clothes & Shopping": {
        "notes": """
        <h4>👕 Shopping Vocabulary - "How much..."</h4>
        <p><strong>Asking about price:</strong></p>
        <ul>
            <li>"<strong>How much</strong> is this shirt?"</li>
            <li>"<strong>How much</strong> does it cost?"</li>
            <li>"<strong>How much</strong> are these shoes?"</li>
        </ul>
        <p><strong>Making decisions:</strong></p>
        <ul>
            <li>"I <strong>will take</strong> it."</li>
            <li>"I <strong>will buy</strong> this one."</li>
        </ul>
        """,
        "examples": [
            "How much is this blue shirt?",
            "I will take it. Where can I pay?",
            "These shoes are too expensive."
        ]
    },
    "Colors & Sizes": {
        "notes": """
        <h4>🎨 Describing Clothes - Adjectives</h4>
        <p><strong>Order of adjectives:</strong></p>
        <ul>
            <li>"A <strong>beautiful</strong> <strong>blue</strong> dress."</li>
            <li>"<strong>Large</strong> <strong>black</strong> shoes."</li>
            <li>"<strong>Nice</strong> <strong>white</strong> shirt."</li>
        </ul>
        <p><strong>Sizes:</strong></p>
        <ul>
            <li>S = Small, M = Medium, L = Large, XL = Extra Large</li>
        </ul>
        """,
        "examples": [
            "Do you have this in a larger size?",
            "I need a medium blue shirt.",
            "The red dress looks beautiful."
        ]
    },
    "Payment & Returns": {
        "notes": """
        <h4>💳 Payment and Return Policies</h4>
        <p><strong>At the checkout:</strong></p>
        <ul>
            <li>"I'd like to buy these items."</li>
            <li>"Can I pay by card?"</li>
            <li>"Do you have a return policy?"</li>
        </ul>
        <p><strong>Returns:</strong></p>
        <ul>
            <li>"I would like to return this."</li>
            <li>"The size is wrong."</li>
            <li>"Can I get a refund?"</li>
        </ul>
        """,
        "examples": [
            "I'd like to buy these two shirts.",
            "Can I pay by card?",
            "I would like to return this. It's too small."
        ]
    }
}

VOCABULARY_DATA = {

    "Airport Vocabulary": [
        {"word": "Airport", "pronunciation": "/ˈeəpɔːt/", "meaning": "A place where planes take off and land",
         "meaning_fa": "فرودگاه", "part_of_speech": "Noun", "example": "I am going to the airport.",
         "example_fa": "من به فرودگاه می‌روم."},
        {"word": "Terminal", "pronunciation": "/ˈtɜːmɪnl/", "meaning": "A building where passengers arrive and depart",
         "meaning_fa": "ترمینال", "part_of_speech": "Noun", "example": "We arrived at terminal 3.",
         "example_fa": "ما به ترمینال ۳ رسیدیم."},
        {"word": "Gate", "pronunciation": "/ɡeɪt/", "meaning": "The entrance to the plane", "meaning_fa": "گیت",
         "part_of_speech": "Noun", "example": "Our flight is at gate B5.", "example_fa": "پرواز ما در گیت B5 است."},
        {"word": "Boarding pass", "pronunciation": "/ˈbɔːdɪŋ pɑːs/",
         "meaning": "A document that allows you to board the plane", "meaning_fa": "کارت سوار شدن",
         "part_of_speech": "Noun", "example": "Please show your boarding pass.",
         "example_fa": "لطفاً کارت سوار شدن خود را نشان دهید."},
        {"word": "Check-in", "pronunciation": "/ˈtʃek ɪn/", "meaning": "The process of registering at the airport",
         "meaning_fa": "ثبت‌نام", "part_of_speech": "Noun", "example": "We need to check in before the flight.",
         "example_fa": "ما باید قبل از پرواز ثبت‌نام کنیم."}
    ],
    "Checking In": [
        {"word": "Passport", "pronunciation": "/ˈpɑːspɔːt/", "meaning": "A document that identifies you as a citizen",
         "meaning_fa": "پاسپورت", "part_of_speech": "Noun", "example": "Please show me your passport.",
         "example_fa": "لطفاً پاسپورت خود را نشان دهید."},
        {"word": "Ticket", "pronunciation": "/ˈtɪkɪt/", "meaning": "A document that allows you to travel",
         "meaning_fa": "بلیط", "part_of_speech": "Noun", "example": "I have an e-ticket for the flight.",
         "example_fa": "من بلیط الکترونیکی برای پرواز دارم."},
        {"word": "Luggage", "pronunciation": "/ˈlʌɡɪdʒ/", "meaning": "Bags and suitcases for travel",
         "meaning_fa": "چمدان", "part_of_speech": "Noun", "example": "How many pieces of luggage do you have?",
         "example_fa": "چند تکه چمدان دارید؟"}
    ],
    "Security & Boarding": [
        {"word": "Security", "pronunciation": "/sɪˈkjʊərəti/", "meaning": "Measures to protect against danger",
         "meaning_fa": "امنیت", "part_of_speech": "Noun", "example": "We need to go through security.",
         "example_fa": "ما باید از امنیت عبور کنیم."},
        {"word": "Detector", "pronunciation": "/dɪˈtektər/", "meaning": "A device that finds something",
         "meaning_fa": "دستگاه تشخیص", "part_of_speech": "Noun", "example": "Walk through the metal detector.",
         "example_fa": "از فلزیاب عبور کنید."},
        {"word": "Board", "pronunciation": "/bɔːd/", "meaning": "To get on a plane, ship, or train",
         "meaning_fa": "سوار شدن", "part_of_speech": "Verb", "example": "We will board the plane at 10:30.",
         "example_fa": "ما ساعت ۱۰:۳۰ سوار هواپیما می‌شویم."}
    ],
    "Arrivals & Baggage": [
        {"word": "Arrival", "pronunciation": "/əˈraɪvl/", "meaning": "The act of coming to a place",
         "meaning_fa": "ورود", "part_of_speech": "Noun", "example": "We arrived at our destination.",
         "example_fa": "ما به مقصد خود رسیدیم."},
        {"word": "Baggage", "pronunciation": "/ˈbæɡɪdʒ/", "meaning": "Luggage and bags", "meaning_fa": "بار",
         "part_of_speech": "Noun", "example": "Go to the baggage claim area.",
         "example_fa": "به محوطه دریافت بار بروید."},
        {"word": "Carousel", "pronunciation": "/ˌkærəˈsel/", "meaning": "A moving belt that carries luggage",
         "meaning_fa": "نوار گردان بار", "part_of_speech": "Noun", "example": "The bags come out on the carousel.",
         "example_fa": "چمدان‌ها روی نوار گردان بیرون می‌آیند."}
    ],
    "In-Flight Experience": [
        {"word": "Flight attendant", "pronunciation": "/flaɪt əˈtendənt/",
         "meaning": "A person who serves passengers on a plane", "meaning_fa": "مهماندار", "part_of_speech": "Noun",
         "example": "The flight attendant brought drinks.", "example_fa": "مهماندار نوشیدنی آورد."},
        {"word": "Takeoff", "pronunciation": "/ˈteɪkɒf/", "meaning": "The moment a plane leaves the ground",
         "meaning_fa": "برخاستن", "part_of_speech": "Noun", "example": "The plane is ready for takeoff.",
         "example_fa": "هواپیما آماده برخاستن است."},
        {"word": "Landing", "pronunciation": "/ˈlændɪŋ/", "meaning": "The moment a plane returns to the ground",
         "meaning_fa": "فرود", "part_of_speech": "Noun", "example": "We will have a smooth landing.",
         "example_fa": "ما فرود خوبی خواهیم داشت."}
    ],


    "Menu & Ordering": [
        {"word": "Menu", "pronunciation": "/ˈmenjuː/", "meaning": "A list of food and drinks", "meaning_fa": "منو",
         "part_of_speech": "Noun", "example": "Can I see the menu, please?", "example_fa": "می‌توانم منو را ببینم؟"},
        {"word": "Appetizer", "pronunciation": "/ˈæpɪtaɪzər/", "meaning": "A small dish before the main meal",
         "meaning_fa": "پیش‌غذا", "part_of_speech": "Noun", "example": "I'll have the appetizer.",
         "example_fa": "من پیش‌غذا می‌خواهم."},
        {"word": "Main course", "pronunciation": "/meɪn kɔːs/", "meaning": "The main dish of a meal",
         "meaning_fa": "غذای اصلی", "part_of_speech": "Noun", "example": "The main course is grilled salmon.",
         "example_fa": "غذای اصلی ماهی سالمون کبابی است."}
    ],
    "Table Conversation": [
        {"word": "Waiter", "pronunciation": "/ˈweɪtər/", "meaning": "A person who serves food at a restaurant",
         "meaning_fa": "گارسون", "part_of_speech": "Noun", "example": "The waiter took our order.",
         "example_fa": "گارسون سفارش ما را گرفت."},
        {"word": "Customer", "pronunciation": "/ˈkʌstəmər/", "meaning": "A person who buys something",
         "meaning_fa": "مشتری", "part_of_speech": "Noun", "example": "The customer asked for the bill.",
         "example_fa": "مشتری صورتحساب را خواست."},
        {"word": "Reservation", "pronunciation": "/ˌrezəˈveɪʃn/", "meaning": "A booking for a table",
         "meaning_fa": "رزرو", "part_of_speech": "Noun", "example": "I have a reservation for 8 PM.",
         "example_fa": "من رزرو برای ساعت ۸ شب دارم."}
    ],
    "Paying the Bill": [
        {"word": "Bill", "pronunciation": "/bɪl/", "meaning": "A piece of paper showing how much you need to pay",
         "meaning_fa": "صورتحساب", "part_of_speech": "Noun", "example": "Could we have the bill, please?",
         "example_fa": "می‌توانیم صورتحساب را داشته باشیم؟"},
        {"word": "Credit card", "pronunciation": "/ˈkredɪt kɑːd/", "meaning": "A card used to pay for things",
         "meaning_fa": "کارت اعتباری", "part_of_speech": "Noun", "example": "Do you accept credit cards?",
         "example_fa": "کارت اعتباری قبول می‌کنید؟"},
        {"word": "Change", "pronunciation": "/tʃeɪndʒ/", "meaning": "Money returned after payment",
         "meaning_fa": "بقیه پول", "part_of_speech": "Noun", "example": "Keep the change.",
         "example_fa": "بقیه پول را نگه دارید."}
    ],
    "Food & Culture": [
        {"word": "Cuisine", "pronunciation": "/kwɪˈziːn/", "meaning": "A style of cooking", "meaning_fa": "سبک آشپزی",
         "part_of_speech": "Noun", "example": "Italian cuisine is my favorite.",
         "example_fa": "سبک آشپزی ایتالیایی مورد علاقه من است."},
        {"word": "Chopsticks", "pronunciation": "/ˈtʃɒpstɪks/", "meaning": "Two sticks used for eating in Asia",
         "meaning_fa": "چاپ‌ستیک", "part_of_speech": "Noun", "example": "We use chopsticks in Japan.",
         "example_fa": "در ژاپن از چاپ‌ستیک استفاده می‌کنیم."},
        {"word": "Spicy", "pronunciation": "/ˈspaɪsi/", "meaning": "Having a strong hot flavor", "meaning_fa": "تند",
         "part_of_speech": "Adjective", "example": "This food is very spicy.", "example_fa": "این غذا خیلی تند است."}
    ],


    "Clothes & Shopping": [
        {"word": "Shirt", "pronunciation": "/ʃɜːt/", "meaning": "A piece of clothing for the upper body",
         "meaning_fa": "پیراهن", "part_of_speech": "Noun", "example": "I bought a blue shirt.",
         "example_fa": "من یک پیراهن آبی خریدم."},
        {"word": "Dress", "pronunciation": "/dres/", "meaning": "A piece of clothing for women",
         "meaning_fa": "لباس زنانه", "part_of_speech": "Noun", "example": "She is wearing a beautiful dress.",
         "example_fa": "او یک لباس زیبا پوشیده است."},
        {"word": "Shoes", "pronunciation": "/ʃuːz/", "meaning": "Things you wear on your feet", "meaning_fa": "کفش",
         "part_of_speech": "Noun", "example": "These shoes are very comfortable.",
         "example_fa": "این کفش‌ها خیلی راحت هستند."}
    ],
    "Colors & Sizes": [
        {"word": "Size", "pronunciation": "/saɪz/", "meaning": "How big or small something is", "meaning_fa": "سایز",
         "part_of_speech": "Noun", "example": "What size do you need?", "example_fa": "چه سایزی نیاز دارید؟"},
        {"word": "Fitting room", "pronunciation": "/ˈfɪtɪŋ ruːm/", "meaning": "A room to try on clothes",
         "meaning_fa": "اتاق پرو", "part_of_speech": "Noun", "example": "The fitting room is over there.",
         "example_fa": "اتاق پرو آنجاست."},
        {"word": "Discount", "pronunciation": "/ˈdɪskaʊnt/", "meaning": "A reduction in price", "meaning_fa": "تخفیف",
         "part_of_speech": "Noun", "example": "There is a 20% discount today.",
         "example_fa": "امروز ۲۰٪ تخفیف وجود دارد."}
    ],
    "Payment & Returns": [
        {"word": "Refund", "pronunciation": "/ˈriːfʌnd/", "meaning": "Money returned when you return an item",
         "meaning_fa": "بازپرداخت", "part_of_speech": "Noun", "example": "I want a refund for this item.",
         "example_fa": "من بازپرداخت برای این کالا می‌خواهم."},
        {"word": "Receipt", "pronunciation": "/rɪˈsiːt/", "meaning": "A paper showing proof of payment",
         "meaning_fa": "رسید", "part_of_speech": "Noun", "example": "Can I have a receipt, please?",
         "example_fa": "می‌توانم یک رسید داشته باشم؟"},
        {"word": "Exchange", "pronunciation": "/ɪksˈtʃeɪndʒ/", "meaning": "To return an item and get a different one",
         "meaning_fa": "تعویض", "part_of_speech": "Verb", "example": "I want to exchange this shirt.",
         "example_fa": "من می‌خواهم این پیراهن را تعویض کنم."}
    ]
}


@transaction.atomic
def create_worlds():
    worlds = []

    world1, created = World.objects.get_or_create(
        name="Airport Adventures",
        defaults={
            "name_fa": "ماجراهای فرودگاه",
            "description": "Learn English for traveling through airports - from check-in to boarding and arrivals",
            "difficulty_level": "A1",
            "order": 1,
            "xp_reward": 500,
            "coin_reward": 100,
            "is_published": True,
        }
    )
    worlds.append(world1)

    world2, created = World.objects.get_or_create(
        name="Restaurant & Food",
        defaults={
            "name_fa": "رستوران و غذا",
            "description": "Learn English for dining out - ordering food, understanding menus, and making reservations",
            "difficulty_level": "A1",
            "order": 2,
            "xp_reward": 500,
            "coin_reward": 100,
            "is_published": True,
        }
    )
    worlds.append(world2)

    print(f"✅ {len(worlds)} جهان ایجاد شد")
    return worlds


@transaction.atomic
def create_chapters_and_lessons(worlds):
    all_chapters = []
    all_lessons = []
    chapter_index = 1


    chapter1_1, created = Chapter.objects.get_or_create(
        world=worlds[0],
        order=1,
        defaults={
            "name": "Airport Basics",
            "name_fa": "مبانی فرودگاه",
            "description": "Learn basic airport vocabulary and how to check in for your flight",
            "unlock_score": 0,
            "xp_reward": 100,
            "coin_reward": 20,
            "passing_score": 70,
            "estimated_time_minutes": 30,
            "is_published": True,
        }
    )
    all_chapters.append(chapter1_1)

    chapter1_2, created = Chapter.objects.get_or_create(
        world=worlds[0],
        order=2,
        defaults={
            "name": "Flight Experience",
            "name_fa": "تجربه پرواز",
            "description": "Learn about security, boarding, and in-flight experience",
            "unlock_score": 70,
            "xp_reward": 120,
            "coin_reward": 25,
            "passing_score": 70,
            "estimated_time_minutes": 35,
            "is_published": True,
        }
    )
    all_chapters.append(chapter1_2)

    chapter1_3, created = Chapter.objects.get_or_create(
        world=worlds[0],
        order=3,
        defaults={
            "name": "Arrivals & Delays",
            "name_fa": "ورود و تاخیرها",
            "description": "Learn about baggage claim, customs, and dealing with flight delays",
            "unlock_score": 70,
            "xp_reward": 120,
            "coin_reward": 25,
            "passing_score": 70,
            "estimated_time_minutes": 35,
            "is_published": True,
        }
    )
    all_chapters.append(chapter1_3)


    chapter2_1, created = Chapter.objects.get_or_create(
        world=worlds[1],
        order=1,
        defaults={
            "name": "Dining Out",
            "name_fa": "غذا خوردن بیرون",
            "description": "Learn how to order food and have conversations at restaurants",
            "unlock_score": 0,
            "xp_reward": 100,
            "coin_reward": 20,
            "passing_score": 70,
            "estimated_time_minutes": 30,
            "is_published": True,
        }
    )
    all_chapters.append(chapter2_1)

    chapter2_2, created = Chapter.objects.get_or_create(
        world=worlds[1],
        order=2,
        defaults={
            "name": "Food Culture",
            "name_fa": "فرهنگ غذا",
            "description": "Learn about international cuisines and cooking at home",
            "unlock_score": 70,
            "xp_reward": 120,
            "coin_reward": 25,
            "passing_score": 70,
            "estimated_time_minutes": 35,
            "is_published": True,
        }
    )
    all_chapters.append(chapter2_2)

    chapter2_3, created = Chapter.objects.get_or_create(
        world=worlds[1],
        order=3,
        defaults={
            "name": "Shopping & Food",
            "name_fa": "خرید و غذا",
            "description": "Learn about buying clothes, colors, sizes, and payments",
            "unlock_score": 70,
            "xp_reward": 120,
            "coin_reward": 25,
            "passing_score": 70,
            "estimated_time_minutes": 35,
            "is_published": True,
        }
    )
    all_chapters.append(chapter2_3)


    lessons_1_1 = [
        {"name": "Airport Vocabulary", "type": "vocabulary", "grammar_key": "Airport Vocabulary",
         "vocab_key": "Airport Vocabulary"},
        {"name": "Checking In", "type": "dialogue", "grammar_key": "Checking In", "vocab_key": "Checking In"},
        {"name": "Security & Boarding", "type": "mixed", "grammar_key": "Security & Boarding",
         "vocab_key": "Security & Boarding"},
    ]
    for i, data in enumerate(lessons_1_1, 1):
        lesson = create_lesson(
            chapter1_1, data["name"], data["type"], i,
            data["grammar_key"], data["vocab_key"]
        )
        all_lessons.append(lesson)
        create_quiz_for_lesson(lesson)


    lessons_1_2 = [
        {"name": "Arrivals & Baggage", "type": "reading", "grammar_key": "Arrivals & Baggage",
         "vocab_key": "Arrivals & Baggage"},
        {"name": "In-Flight Experience", "type": "listening", "grammar_key": "In-Flight Experience",
         "vocab_key": "In-Flight Experience"},
        {"name": "Flight Delays", "type": "speaking", "grammar_key": "Flight Delays",
         "vocab_key": "In-Flight Experience"},
    ]
    for i, data in enumerate(lessons_1_2, 1):
        lesson = create_lesson(
            chapter1_2, data["name"], data["type"], i,
            data["grammar_key"], data["vocab_key"]
        )
        all_lessons.append(lesson)
        create_quiz_for_lesson(lesson)


    lessons_1_3 = [
        {"name": "Arrivals & Baggage", "type": "reading", "grammar_key": "Arrivals & Baggage",
         "vocab_key": "Arrivals & Baggage"},
        {"name": "In-Flight Experience", "type": "listening", "grammar_key": "In-Flight Experience",
         "vocab_key": "In-Flight Experience"},
        {"name": "Flight Delays", "type": "speaking", "grammar_key": "Flight Delays",
         "vocab_key": "In-Flight Experience"},
    ]
    for i, data in enumerate(lessons_1_3, 1):
        lesson = create_lesson(
            chapter1_3, data["name"], data["type"], i,
            data["grammar_key"], data["vocab_key"]
        )
        all_lessons.append(lesson)
        create_quiz_for_lesson(lesson)


    lessons_2_1 = [
        {"name": "Menu & Ordering", "type": "vocabulary", "grammar_key": "Menu & Ordering",
         "vocab_key": "Menu & Ordering"},
        {"name": "Table Conversation", "type": "dialogue", "grammar_key": "Table Conversation",
         "vocab_key": "Table Conversation"},
        {"name": "Paying the Bill", "type": "mixed", "grammar_key": "Paying the Bill", "vocab_key": "Paying the Bill"},
    ]
    for i, data in enumerate(lessons_2_1, 1):
        lesson = create_lesson(
            chapter2_1, data["name"], data["type"], i,
            data["grammar_key"], data["vocab_key"]
        )
        all_lessons.append(lesson)
        create_quiz_for_lesson(lesson)


    lessons_2_2 = [
        {"name": "Food & Culture", "type": "reading", "grammar_key": "Food & Culture", "vocab_key": "Food & Culture"},
        {"name": "Cooking at Home", "type": "writing", "grammar_key": "Cooking at Home", "vocab_key": "Food & Culture"},
        {"name": "Restaurant Review", "type": "speaking", "grammar_key": "Restaurant Review",
         "vocab_key": "Food & Culture"},
    ]
    for i, data in enumerate(lessons_2_2, 1):
        lesson = create_lesson(
            chapter2_2, data["name"], data["type"], i,
            data["grammar_key"], data["vocab_key"]
        )
        all_lessons.append(lesson)
        create_quiz_for_lesson(lesson)


    lessons_2_3 = [
        {"name": "Clothes & Shopping", "type": "vocabulary", "grammar_key": "Clothes & Shopping",
         "vocab_key": "Clothes & Shopping"},
        {"name": "Colors & Sizes", "type": "dialogue", "grammar_key": "Colors & Sizes", "vocab_key": "Colors & Sizes"},
        {"name": "Payment & Returns", "type": "mixed", "grammar_key": "Payment & Returns",
         "vocab_key": "Payment & Returns"},
    ]
    for i, data in enumerate(lessons_2_3, 1):
        lesson = create_lesson(
            chapter2_3, data["name"], data["type"], i,
            data["grammar_key"], data["vocab_key"]
        )
        all_lessons.append(lesson)
        create_quiz_for_lesson(lesson)


    for chapter in all_chapters:
        create_chapter_exam(
            chapter,
            f"{chapter.name} Exam",
            f"Test your knowledge of {chapter.name}",
            70, 20
        )

    print(f"✅ {len(all_chapters)} فصل و {len(all_lessons)} درس ایجاد شد")
    return all_chapters, all_lessons


def create_lesson(chapter, name, lesson_type, order, grammar_key, vocab_key):


    lesson_data = {
        "name": name,
        "name_fa": name,
        "lesson_type": lesson_type,
        "order": order,
        "xp_reward": 50,
        "coin_reward": 10,
        "estimated_time_minutes": 15,
        "is_published": True,
        "introduction": f"Welcome to {name}! In this lesson, you'll learn essential vocabulary and grammar.",
        "introduction_fa": f"به درس {name} خوش آمدید!",
        "learning_objectives": [
            f"Learn key vocabulary about {name}",
            "Understand grammar structures",
            "Practice speaking and writing"
        ],
        "summary": f"Great job completing {name}!",
        "reading_text": f"This is the reading text for {name}. Practice your reading skills here.",
        "reading_translation": f"متن خواندن برای {name}.",
        "reading_notes": f"Key points for {name}"
    }

    lesson, created = Lesson.objects.get_or_create(
        chapter=chapter,
        order=order,
        defaults={
            "name": lesson_data["name"],
            "name_fa": lesson_data["name_fa"],
            "lesson_type": lesson_data["lesson_type"],
            "xp_reward": lesson_data["xp_reward"],
            "coin_reward": lesson_data["coin_reward"],
            "estimated_time_minutes": lesson_data["estimated_time_minutes"],
            "is_published": lesson_data["is_published"],
            # Only the very first lesson of the very first chapter of the very
            # first world is a free preview; everything else is progression-gated.
            "is_free_preview": bool(
                world.order == 1 and chapter.order == 1 and order == 1
            ),
        }
    )


    content, content_created = LessonContent.objects.get_or_create(
        lesson=lesson,
        defaults={
            "introduction": lesson_data["introduction"],
            "learning_objectives": lesson_data["learning_objectives"],
            "summary": lesson_data["summary"],
            "reading_text": lesson_data["reading_text"],
            "reading_translation": lesson_data["reading_translation"],
            "reading_notes": lesson_data["reading_notes"],
            "is_interactive": True,
            "allow_skip": False,
        }
    )


    if grammar_key in GRAMMAR_DATA:
        grammar = GRAMMAR_DATA[grammar_key]
        content.grammar_notes = grammar["notes"]
        content.grammar_examples = grammar["examples"]
        content.save()


    if vocab_key in VOCABULARY_DATA:
        add_vocabulary_to_lesson(lesson, VOCABULARY_DATA[vocab_key])

    return lesson


def add_vocabulary_to_lesson(lesson, words_data):

    category, _ = VocabularyCategory.objects.get_or_create(
        name=lesson.name[:50],
        defaults={
            "name_fa": lesson.name_fa or lesson.name,
            "description": f"Vocabulary for {lesson.name}",
            "order": lesson.order,
        }
    )

    for data in words_data:
        vocab, created = Vocabulary.objects.get_or_create(
            word=data["word"],
            defaults={
                "pronunciation": data.get("pronunciation", ""),
                "meaning": data["meaning"],
                "meaning_fa": data.get("meaning_fa", ""),
                "part_of_speech": data.get("part_of_speech", ""),
                "difficulty": "A1",
                "is_active": True,
            }
        )
        vocab.categories.add(category)


        if "example" in data:
            VocabularyExample.objects.get_or_create(
                vocabulary=vocab,
                defaults={
                    "sentence": data["example"],
                    "sentence_fa": data.get("example_fa", ""),
                }
            )


def create_quiz_for_lesson(lesson):
    quiz, created = Quiz.objects.get_or_create(
        lesson=lesson,
        defaults={
            "title": f"Quiz: {lesson.name}",
            "description": f"Test your knowledge of {lesson.name}",
            "passing_score": 70,
            "time_limit_minutes": 10,
            "max_attempts": 3,
            "shuffle_questions": True,
            "xp_reward": 30,
            "coin_reward": 15,
            "is_published": True,
        }
    )

    if created:

        questions_data = [
            {
                "type": "mcq",
                "text": f"What is the main topic of {lesson.name}?",
                "text_fa": f"موضوع اصلی {lesson.name} چیست؟",
                "points": 10,
                "order": 0,
                "explanation": f"The main topic of {lesson.name} is related to everyday situations.",
                "choices": [
                    {"text": "Daily life", "is_correct": True},
                    {"text": "Science", "is_correct": False},
                    {"text": "History", "is_correct": False},
                    {"text": "Art", "is_correct": False},
                ]
            },
            {
                "type": "mcq",
                "text": f"Which word is related to {lesson.name}?",
                "text_fa": f"کدام کلمه به {lesson.name} مرتبط است؟",
                "points": 10,
                "order": 1,
                "explanation": "This word is commonly used in this topic.",
                "choices": [
                    {"text": "Travel", "is_correct": True},
                    {"text": "Mathematics", "is_correct": False},
                    {"text": "Geography", "is_correct": False},
                    {"text": "Literature", "is_correct": False},
                ]
            },
            {
                "type": "mcq",
                "text": "What is a key skill in this lesson?",
                "text_fa": "مهارت کلیدی در این درس چیست؟",
                "points": 10,
                "order": 2,
                "explanation": "Communication is a key skill in this lesson.",
                "choices": [
                    {"text": "Communication", "is_correct": True},
                    {"text": "Cooking", "is_correct": False},
                    {"text": "Dancing", "is_correct": False},
                    {"text": "Singing", "is_correct": False},
                ]
            }
        ]

        for q_data in questions_data:
            question = Question.objects.create(
                quiz=quiz,
                question_type=q_data["type"],
                question_text=q_data["text"],
                question_text_fa=q_data.get("text_fa", ""),
                points=q_data.get("points", 10),
                order=q_data.get("order", 0),
                explanation=q_data.get("explanation", ""),
            )
            for choice_data in q_data.get("choices", []):
                QuestionChoice.objects.create(
                    question=question,
                    choice_text=choice_data["text"],
                    choice_text_fa=choice_data.get("text_fa", ""),
                    is_correct=choice_data.get("is_correct", False),
                    order=choice_data.get("order", 0),
                )

    return quiz


def create_chapter_exam(chapter, title, description, passing_score, question_count):
    exam, created = Exam.objects.get_or_create(
        chapter=chapter,
        exam_type="chapter",
        defaults={
            "title": title,
            "description": description,
            "passing_score": passing_score,
            "time_limit_minutes": 30,
            "max_attempts": 3,
            "questions_count": question_count,
            "randomize_questions": True,
            "xp_reward": 200,
            "coin_reward": 50,
            "is_published": True,
        }
    )

    if created:
        exam_questions = [
            {
                "question": f"What is the main topic of {chapter.name}?",
                "question_fa": f"موضوع اصلی {chapter.name} چیست؟",
                "type": "mcq",
                "correct_answer": "It is about everyday situations",
                "options": ["Everyday situations", "Science", "History", "Art"],
                "points": 10,
                "order": 0,
            },
            {
                "question": f"Which skill is important in {chapter.name}?",
                "question_fa": f"کدام مهارت در {chapter.name} مهم است؟",
                "type": "mcq",
                "correct_answer": "Communication",
                "options": ["Communication", "Cooking", "Dancing", "Singing"],
                "points": 10,
                "order": 1,
            },
            {
                "question": f"What is a key word in {chapter.name}?",
                "question_fa": f"کلمه کلیدی در {chapter.name} چیست؟",
                "type": "mcq",
                "correct_answer": "Travel",
                "options": ["Travel", "Mathematics", "Geography", "Literature"],
                "points": 10,
                "order": 2,
            },
            {
                "question": f"Why is {chapter.name} useful?",
                "question_fa": f"چرا {chapter.name} مفید است؟",
                "type": "mcq",
                "correct_answer": "It helps in daily life",
                "options": ["Daily life", "Work only", "School only", "Hobbies"],
                "points": 10,
                "order": 3,
            },
        ]

        while len(exam_questions) < question_count:
            exam_questions.append({
                "question": f"Sample question {len(exam_questions) + 1}",
                "question_fa": f"سوال نمونه {len(exam_questions) + 1}",
                "type": "mcq",
                "correct_answer": "Option A",
                "options": ["Option A", "Option B", "Option C", "Option D"],
                "points": 10,
                "order": len(exam_questions),
            })

        for q_data in exam_questions[:question_count]:
            ExamQuestion.objects.create(
                exam=exam,
                question=q_data["question"],
                question_fa=q_data.get("question_fa", ""),
                question_type=q_data["type"],
                correct_answer=q_data["correct_answer"],
                options=q_data["options"],
                points=q_data.get("points", 10),
                order=q_data.get("order", 0),
            )

    return exam


@transaction.atomic
def create_dialogues():
    for lesson in Lesson.objects.filter(is_published=True)[:10]:
        dialogue, created = Dialogue.objects.get_or_create(
            lesson=lesson,
            defaults={
                "title": f"Dialogue: {lesson.name}",
                "title_fa": f"دیالوگ: {lesson.name}",
                "description": f"Practice conversation about {lesson.name}",
                "difficulty": "A1",
                "is_active": True,
                "order": 1,
            }
        )

        if created:

            scene1, _ = DialogueScene.objects.get_or_create(
                dialogue=dialogue,
                order=1,
                defaults={
                    "character": "Person A",
                    "message": f"Hello! Let's talk about {lesson.name}.",
                    "message_fa": f"سلام! بیایید در مورد {lesson.name} صحبت کنیم.",
                    "is_user_turn": False,
                }
            )

            scene2, _ = DialogueScene.objects.get_or_create(
                dialogue=dialogue,
                order=2,
                defaults={
                    "character": "Person B",
                    "message": f"That sounds interesting. Can you tell me more?",
                    "message_fa": f"این جالب به نظر می‌رسد. می‌توانید بیشتر توضیح دهید؟",
                    "is_user_turn": True,
                }
            )

            DialogueChoice.objects.get_or_create(
                scene=scene2,
                defaults={
                    "choice_text": "Yes, let me explain.",
                    "choice_text_fa": "بله، اجازه دهید توضیح دهم.",
                    "is_correct": True,
                    "feedback": "Good! Continue the conversation.",
                    "feedback_fa": "خوب! مکالمه را ادامه دهید.",
                    "xp_reward": 5,
                }
            )

    print(f"✅ دیالوگ‌ها ایجاد شد")


@transaction.atomic
def create_badges():
    badges_data = [
        {"name": "Airport Explorer", "name_fa": "کاشف فرودگاه", "description": "Completed the Airport chapter",
         "badge_type": "world", "requirement_type": "chapter_completion", "requirement_value": 1, "xp_reward": 50,
         "order": 1},
        {"name": "Flight Master", "name_fa": "استاد پرواز", "description": "Completed the Flight Experience chapter",
         "badge_type": "world", "requirement_type": "chapter_completion", "requirement_value": 1, "xp_reward": 60,
         "order": 2},
        {"name": "Food Lover", "name_fa": "عاشق غذا", "description": "Completed the Food chapter",
         "badge_type": "world", "requirement_type": "chapter_completion", "requirement_value": 1, "xp_reward": 50,
         "order": 3},
        {"name": "Chef", "name_fa": "آشپز", "description": "Completed the Cooking chapter", "badge_type": "world",
         "requirement_type": "chapter_completion", "requirement_value": 1, "xp_reward": 60, "order": 4},
        {"name": "Shopper", "name_fa": "خریدار", "description": "Completed the Shopping chapter", "badge_type": "world",
         "requirement_type": "chapter_completion", "requirement_value": 1, "xp_reward": 50, "order": 5},
        {"name": "First Flight", "name_fa": "اولین پرواز", "description": "Completed your first lesson",
         "badge_type": "milestone", "requirement_type": "lesson_completion", "requirement_value": 1, "xp_reward": 25,
         "order": 6},
        {"name": "Grammar Expert", "name_fa": "متخصص گرامر", "description": "Completed 10 grammar exercises",
         "badge_type": "mastery", "requirement_type": "grammar_completion", "requirement_value": 10, "xp_reward": 40,
         "order": 7},
        {"name": "Vocabulary Master", "name_fa": "استاد واژگان", "description": "Learned 50 new words",
         "badge_type": "mastery", "requirement_type": "vocabulary_mastery", "requirement_value": 50, "xp_reward": 40,
         "order": 8},
    ]

    for data in badges_data:
        Badge.objects.get_or_create(
            name=data["name"],
            defaults={
                "name_fa": data.get("name_fa", ""),
                "description": data["description"],
                "badge_type": data["badge_type"],
                "requirement_type": data["requirement_type"],
                "requirement_value": data["requirement_value"],
                "xp_reward": data["xp_reward"],
                "is_active": True,
                "order": data["order"],
            }
        )

    print(f"✅ مدال‌ها ایجاد شد")


def run():
    print("🚀 شروع به پر کردن کامل دیتابیس...")
    print("=" * 60)

    try:

        worlds = create_worlds()
        print()


        chapters, lessons = create_chapters_and_lessons(worlds)
        print()


        create_dialogues()
        print()


        create_badges()
        print()

        print("=" * 60)
        print("✅✅✅ دیتابیس با موفقیت پر شد!")
        print(f"\n📊 خلاصه نهایی:")
        print(f"   🌍 {len(worlds)} جهان")
        print(f"   📚 {len(chapters)} فصل")
        print(f"   📖 {len(lessons)} درس")
        print(f"   📝 {len(GRAMMAR_DATA)} درس دارای گرامر")
        print(f"   📚 {len(VOCABULARY_DATA)} درس دارای واژگان")
        print(f"   🏆 {Badge.objects.count()} مدال")
        print(f"   💬 {Dialogue.objects.count()} دیالوگ")
        print("=" * 60)

    except Exception as e:
        print(f"❌ خطا: {e}")
        import traceback
        traceback.print_exc()
        raise


if __name__ == "__main__":
    run()
