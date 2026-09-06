from itertools import product
import re


def _generate_questions(templates, slots):
    results = []
    for template in templates:
        keys = re.findall(r"{(.*?)}", template)
        if not keys:
            results.append(template)
            continue
        values = [slots[key] for key in keys]
        for combo in product(*values):
            data = dict(zip(keys, combo))
            results.append(template.format(**data))

    seen = set()
    unique = []
    for question in results:
        question = " ".join(question.split())
        if question and question not in seen:
            seen.add(question)
            unique.append(question)
    return unique


def _pad_questions(questions, target):
    if not questions:
        return questions

    prefixes = [
        "Can you tell me",
        "Please explain",
        "I want to know",
        "Could you explain",
        "Help me with",
    ]
    idx = 0
    while len(questions) < target:
        base = questions[idx % len(questions)]
        prefix = prefixes[idx % len(prefixes)]
        if base and base[0].isupper():
            base = base[0].lower() + base[1:]
        questions.append(f"{prefix} {base}")
        idx += 1
    return questions


def build_faqs(total_target=500):
    intents = [
        {
            "key": "service_intro",
            "a": "We deliver meals from local restaurants straight to your door.",
            "templates": [
                "What is this {service}?",
                "What does this {service} do?",
                "Tell me about the {service}.",
                "Explain the {service}.",
                "What is this app for?",
            ],
            "slots": {
                "service": [
                    "service",
                    "delivery service",
                    "food delivery app",
                    "platform",
                    "ordering service",
                ]
            },
        },
        {
            "key": "meals_available",
            "a": "You can order any items listed by partner restaurants in the app.",
            "templates": [
                "What meals can I order?",
                "What {items} are available?",
                "What food can I get?",
                "What can I order from the {app}?",
                "Which {items} do you offer?",
            ],
            "slots": {
                "items": ["meals", "dishes", "menu items", "foods", "options"],
                "app": [
                    "app",
                    "service",
                    "platform",
                    "delivery app",
                    "site",
                ],
            },
        },
        {
            "key": "fast_food",
            "a": "Yes, availability depends on which restaurants are near you.",
            "templates": [
                "Do you have {fastfood} options?",
                "Can I order {fastfood}?",
                "Are {fastfood} restaurants available?",
                "Is {fastfood} supported near me?",
                "Do you deliver from {fastfood} places?",
            ],
            "slots": {
                "fastfood": [
                    "fast food",
                    "burger places",
                    "quick service",
                    "takeout chains",
                    "fast casual",
                ]
            },
        },
        {
            "key": "delivery_areas",
            "a": "Enter your address to see if delivery is available in your area.",
            "templates": [
                "What areas do you deliver to?",
                "Where do you deliver?",
                "Is delivery available in my {area}?",
                "Do you deliver to {area_type}?",
                "Which {areas} are covered?",
            ],
            "slots": {
                "area": ["area", "neighborhood", "city", "zip code", "address"],
                "area_type": [
                    "my area",
                    "my city",
                    "my neighborhood",
                    "my zip code",
                    "my address",
                ],
                "areas": ["areas", "zones", "neighborhoods", "cities", "zip codes"],
            },
        },
        {
            "key": "delivery_hours",
            "a": "Delivery is available daily from 10:00 AM to 11:00 PM.",
            "templates": [
                "What are your delivery hours?",
                "When do you {deliver}?",
                "What time do you start and stop {delivering}?",
                "Are you open {hours}?",
                "Do you deliver {when}?",
            ],
            "slots": {
                "deliver": [
                    "deliver",
                    "do deliveries",
                    "operate",
                    "run deliveries",
                    "offer delivery",
                ],
                "delivering": [
                    "delivery",
                    "delivering",
                    "service",
                    "order delivery",
                    "courier delivery",
                ],
                "hours": [
                    "late at night",
                    "every day",
                    "on weekends",
                    "after 10 pm",
                    "in the morning",
                ],
                "when": ["at night", "on weekends", "on holidays", "late", "early"],
            },
        },
        {
            "key": "delivery_time",
            "a": "Most orders arrive in 30 to 45 minutes depending on distance.",
            "templates": [
                "How long does {delivery} take?",
                "What is the {delivery} time?",
                "What is the usual {delivery} ETA?",
                "Average {delivery} time?",
                "When will my order arrive?",
            ],
            "slots": {
                "delivery": [
                    "delivery",
                    "order delivery",
                    "courier delivery",
                    "drop off",
                    "food delivery",
                ]
            },
        },
        {
            "key": "schedule_order",
            "a": "Yes, you can schedule orders up to 7 days in advance.",
            "templates": [
                "Can I schedule an order?",
                "Can I place a {scheduled} order?",
                "Do you allow {scheduled} orders?",
                "How do I {schedule} an order?",
                "Is {schedule} available?",
            ],
            "slots": {
                "scheduled": ["scheduled", "pre-order", "future", "advance", "timed"],
                "schedule": [
                    "scheduling",
                    "pre-ordering",
                    "ordering ahead",
                    "planning ahead",
                    "booking",
                ],
            },
        },
        {
            "key": "promo_code",
            "a": "Add the code at checkout before you place the order.",
            "templates": [
                "How do I apply a {promo} code?",
                "Where do I enter a {promo} code?",
                "Can I use a {promo} code?",
                "My {promo} code is not working",
                "Do you accept {promo} codes?",
            ],
            "slots": {
                "promo": ["promo", "discount", "coupon", "voucher", "referral"]
            },
        },
        {
            "key": "payment_methods",
            "a": "We accept credit cards, debit cards, PayPal, and Apple Pay.",
            "templates": [
                "What payment methods do you accept?",
                "Which {payment} are supported?",
                "Can I pay with {payment}?",
                "Do you take {payment}?",
                "What ways can I pay?",
            ],
            "slots": {
                "payment": [
                    "credit card",
                    "debit card",
                    "PayPal",
                    "Apple Pay",
                    "Google Pay",
                ]
            },
        },
        {
            "key": "cash_delivery",
            "a": "Cash on delivery is available in select areas only.",
            "templates": [
                "Is cash on delivery available?",
                "Can I pay {cash}?",
                "Do you accept {cash} payment?",
                "Is {cash} supported?",
                "Can I give {cash} to the driver?",
            ],
            "slots": {
                "cash": [
                    "cash on delivery",
                    "cash",
                    "cash payment",
                    "cash at the door",
                    "cash at drop off",
                ]
            },
        },
        {
            "key": "track_order",
            "a": "Open your order page to see live driver tracking.",
            "templates": [
                "How do I track my order?",
                "Where can I see {tracking}?",
                "Can I track the {driver}?",
                "How do I follow my delivery?",
                "Is live tracking available?",
            ],
            "slots": {
                "tracking": [
                    "order status",
                    "delivery status",
                    "tracking",
                    "ETA",
                    "order progress",
                ],
                "driver": [
                    "driver",
                    "courier",
                    "rider",
                    "delivery driver",
                    "courier driver",
                ],
            },
        },
        {
            "key": "late_order",
            "a": "Contact support in the app and we will help right away.",
            "templates": [
                "What if my order is late?",
                "My delivery is {late}, what do I do?",
                "What happens if the order is {late}?",
                "Who do I contact about a {late} order?",
                "The driver is late, help",
            ],
            "slots": {
                "late": [
                    "late",
                    "delayed",
                    "taking too long",
                    "behind schedule",
                    "overdue",
                ]
            },
        },
        {
            "key": "missing_items",
            "a": "Report missing items within 24 hours for a quick resolution.",
            "templates": [
                "What if items are missing from my order?",
                "I am missing {item} from my order",
                "Some items are missing, what now?",
                "How do I report {missing} items?",
                "My order is incomplete",
            ],
            "slots": {
                "item": ["an item", "a dish", "a side", "a drink", "a product"],
                "missing": [
                    "missing",
                    "forgotten",
                    "left out",
                    "not delivered",
                    "incomplete",
                ],
            },
        },
        {
            "key": "cancel_order",
            "a": "You can cancel before the restaurant accepts the order.",
            "templates": [
                "How do I cancel an {order}?",
                "Can I cancel my {order}?",
                "Is {order} cancellation possible?",
                "I want to cancel my {order}",
                "How can I stop an {order}?",
            ],
            "slots": {
                "order": ["order", "delivery", "food order", "purchase", "request"]
            },
        },
        {
            "key": "change_order",
            "a": "Changes are possible only before the restaurant starts preparing it.",
            "templates": [
                "Can I change my order after placing it?",
                "How do I edit my {order}?",
                "Can I modify my {order}?",
                "Is it possible to update my {order}?",
                "I need to change my {order}",
            ],
            "slots": {
                "order": ["order", "delivery", "food order", "purchase", "request"]
            },
        },
        {
            "key": "contact_support",
            "a": "Use in app chat or email support@quickbite.example.",
            "templates": [
                "How do I contact customer support?",
                "How can I reach support?",
                "Is there a support {channel}?",
                "Where can I get help?",
                "How do I talk to support?",
            ],
            "slots": {
                "channel": ["chat", "email", "phone", "agent", "team"]
            },
        },
        {
            "key": "delivery_fee",
            "a": "Yes, delivery fees vary based on distance and demand.",
            "templates": [
                "Do you charge {fee} fees?",
                "How much is the {fee} fee?",
                "What is the {fee} cost?",
                "Is there a {fee} fee?",
                "Are {fee} fees extra?",
            ],
            "slots": {
                "fee": ["delivery", "drop off", "courier", "driver", "distance"]
            },
        },
        {
            "key": "service_fee",
            "a": "A small service fee helps keep the platform running.",
            "templates": [
                "Do you charge a {fee} fee?",
                "What is the {fee} fee for?",
                "How much is the {fee} fee?",
                "Is there a {fee} fee?",
                "Why is there a {fee} fee?",
            ],
            "slots": {
                "fee": ["service", "platform", "processing", "app", "order"]
            },
        },
        {
            "key": "tip_driver",
            "a": "Yes, you can add a tip at checkout or after delivery.",
            "templates": [
                "Can I tip the driver?",
                "How do I add a tip?",
                "Is tipping available?",
                "Can I leave a tip for the {driver}?",
                "Where can I tip?",
            ],
            "slots": {
                "driver": [
                    "driver",
                    "courier",
                    "rider",
                    "delivery driver",
                    "courier driver",
                ]
            },
        },
        {
            "key": "refunds",
            "a": "Approved refunds return to the original payment method in 3 to 5 days.",
            "templates": [
                "How do {refund} work?",
                "When will I get my {refund}?",
                "How long do {refund} take?",
                "What is your {refund} policy?",
                "How do I request a {refund}?",
            ],
            "slots": {
                "refund": ["refunds", "refund", "credits", "money back", "reversals"]
            },
        },
        {
            "key": "allergies",
            "a": "Add allergy notes, but always confirm with the restaurant.",
            "templates": [
                "How do you handle {allergy} allergies?",
                "Can I add {allergy} notes?",
                "Is allergy info supported?",
                "What if I have a {allergy} allergy?",
                "How do I report an allergy?",
            ],
            "slots": {
                "allergy": ["food", "nut", "gluten", "dairy", "seafood"]
            },
        },
        {
            "key": "minimum_order",
            "a": "Some restaurants set a minimum order amount.",
            "templates": [
                "Are there minimum order values?",
                "Is there a minimum order?",
                "Do I need to meet a minimum {amount}?",
                "What is the minimum order {amount}?",
                "Is there a minimum spend?",
            ],
            "slots": {
                "amount": ["amount", "value", "price", "total", "spend"]
            },
        },
        {
            "key": "multiple_restaurants",
            "a": "Each order can include items from only one restaurant.",
            "templates": [
                "Can I order from multiple restaurants at once?",
                "Can I combine {restaurants} in one order?",
                "Do you allow orders from {restaurants}?",
                "Can I mix items from {restaurants}?",
                "Is multi-restaurant ordering supported?",
            ],
            "slots": {
                "restaurants": [
                    "multiple restaurants",
                    "different restaurants",
                    "two restaurants",
                    "several restaurants",
                    "more than one restaurant",
                ]
            },
        },
        {
            "key": "subscription_plan",
            "a": "Yes, our Plus plan offers reduced delivery fees each month.",
            "templates": [
                "Do you offer a {plan} plan?",
                "What is your {plan} plan?",
                "Is there a monthly {plan}?",
                "How does the {plan} plan work?",
                "Can I subscribe for lower fees?",
            ],
            "slots": {
                "plan": [
                    "subscription",
                    "Plus",
                    "membership",
                    "monthly",
                    "premium",
                ]
            },
        },
        {
            "key": "receipt_invoice",
            "a": "Yes, a receipt is emailed after every completed order.",
            "templates": [
                "Can I get an {doc} or receipt?",
                "Where is my {doc}?",
                "Do you email {doc}s?",
                "How do I download an {doc}?",
                "Can I get a tax {doc}?",
            ],
            "slots": {
                "doc": ["invoice", "receipt", "order receipt", "tax receipt", "bill"]
            },
        },
        {
            "key": "update_address",
            "a": "Update your address in your profile before placing an order.",
            "templates": [
                "How do I update my delivery address?",
                "Can I change my address?",
                "Where do I edit my delivery {address}?",
                "How do I set a new {address}?",
                "I need to update my {address}",
            ],
            "slots": {
                "address": [
                    "address",
                    "delivery address",
                    "drop off address",
                    "location",
                    "delivery location",
                ]
            },
        },
        {
            "key": "card_declined",
            "a": "Please check with your bank or try another payment method.",
            "templates": [
                "Why was my {payment} declined?",
                "My {payment} was declined, what now?",
                "{payment} failed, why?",
                "Why did the {payment} not go through?",
                "My {payment} is not working",
            ],
            "slots": {
                "payment": ["card", "payment", "transaction", "charge", "order payment"]
            },
        },
        {
            "key": "prices_different",
            "a": "Some restaurants adjust prices for delivery, and taxes or fees may apply.",
            "templates": [
                "Why do {prices} look different from the restaurant menu?",
                "Why are {prices} higher than in store?",
                "Why is the {menu} price different?",
                "Are delivery prices different?",
                "Why is the price higher?",
            ],
            "slots": {
                "prices": [
                    "prices",
                    "menu prices",
                    "item prices",
                    "totals",
                    "amounts",
                ],
                "menu": ["menu", "restaurant", "store", "in store", "original"],
            },
        },
        {
            "key": "total_price",
            "a": "Yes, you see all fees and the final total before placing the order.",
            "templates": [
                "Do you show the {total} before checkout?",
                "Will I see the {total} before I pay?",
                "Can I see all fees before checkout?",
                "Is the {total} shown before ordering?",
                "Do you show the {total} upfront?",
            ],
            "slots": {
                "total": [
                    "total price",
                    "final total",
                    "full price",
                    "total cost",
                    "grand total",
                ]
            },
        },
        {
            "key": "business_accounts",
            "a": "Yes, contact sales@quickbite.example to set up a business account.",
            "templates": [
                "Do you support {business} accounts?",
                "Can I set up a {business} account?",
                "Is there a {business} account option?",
                "Do you offer {business} accounts?",
                "How do I get a {business} account?",
            ],
            "slots": {
                "business": [
                    "business",
                    "corporate",
                    "company",
                    "team",
                    "office",
                ]
            },
        },
    ]

    base = total_target // len(intents)
    extra = total_target % len(intents)
    faqs = []
    for index, intent in enumerate(intents):
        target = base + (1 if index < extra else 0)
        questions = _generate_questions(intent["templates"], intent.get("slots", {}))
        if len(questions) < target:
            questions = _pad_questions(questions, target)
        for question in questions[:target]:
            faqs.append({"q": question, "a": intent["a"]})
    return faqs
