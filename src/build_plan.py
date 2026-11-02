"""Build topic_plan.json: 730 money psychology topics (2 a day for one year), mixed across categories.

The first 60 (month 1) are fixed below; the rest are spread evenly so the same category rarely comes
twice in a row. Dated topics (SEASONAL) are moved to their day. Titles are themes for the weekly writer,
not captions: each one names a real, documented trick or effect, checked again when the script is written.
Set START to the real launch day before going live, then run: python src/build_plan.py
"""
import re
import sys
from datetime import date, timedelta

from common import ROOT, save_json

START = date(2026, 11, 9)  # launch day (the job posts topics in order) — provisional, set the real day before go-live
SLOTS = ["08:00", "20:00"]

CATEGORIES = {
    "Supermarket tricks": """Why the milk is at the back, Eye level is buy level, The shelf at your kid's eye level,
        End of aisle displays, Flowers at the entrance, The smell of fresh bread, Misted vegetables,
        Slow music in the store, The checkout candy trap, Ten for ten dollars deals, Buy one get one free math,
        The unit price label, Store brands made by big brands, Shrinkflation, Loss leaders,
        The cheap rotisserie chicken, Why the pharmacy is at the back, The seasonal aisle,
        Lighting at the meat counter, Shopping while hungry, Shopping with kids, Self checkout psychology,
        Pre cut fruit markup, Bottled water markup, What natural on a label means, Best before dates,
        Multi buy deals that cost more, The bulk buy illusion, The treasure hunt aisle, Bigger shopping carts,
        Free samples, What your loyalty card knows, The weekly flyer, Why stores move products around,
        Baskets versus carts, Mirrors above the vegetables, Why shelves always look full, The dollar store math,
        Smaller packs at dollar stores, Organic labels, The healthy halo, Why coupons make you spend more,
        Digital coupons in store apps, Convenience store prices, Grocery delivery fees, The center aisles,
        Hot food counters, Price match promises, Snack sizes cost more, What fruit stickers tell you, Rain checks,
        Why stores sell cheap gas, Fake farm brands, Scanner errors at the register, Stacked displays,
        Why produce comes first, Meal deal math""",
    "Pricing psychology": """The middle size trap, Why prices end in ninety nine, Anchoring prices,
        The first price you see, Was and now prices, Round prices for treats, The power of free,
        Free shipping thresholds, Bundles that hide prices, Price per month framing, Pennies a day framing,
        Good better best, Prestige pricing, Why expensive wine tastes better, The price and quality myth,
        Dynamic pricing, Surge pricing, Personalized prices, Drip pricing, Junk fees, Resort fees,
        Shipping charged separately, Small fonts for big prices, Red price tags, Left digit bias,
        The expensive item shown first, Why luxury stores hide prices, Pay what you want, The rule of one hundred,
        Twenty percent off twice, Precise prices, Reference prices, Penny auctions, The winner's curse,
        Price match guarantees, Why gas prices end in nine tenths, Prices in a foreign currency,
        The cost of convenience, Why cheap feels risky, Loss framing in prices, The first number wins,
        Anchoring your salary, Concert ticket pricing, Prices before tax, Price discrimination with coupons,
        Price increases you never notice, Odd package sizes, Lucky eight prices, Prices that start from,
        Why products come in versions, The price of a name brand, Pricing by zip code,
        Student and senior discounts, Peak and off peak prices, The word only on price tags,
        Unit prices in different units, The snow shovel price hike""",
    "Restaurants and menus": """Menu engineering, Do you read a menu like a book, Decoy dishes,
        The expensive dish as an anchor, Menus without dollar signs, Long words on fancy menus, Boxes around dishes,
        Photos on menus, The second cheapest wine, Wine markups, Bottled water at restaurants,
        Soda refills cost pennies, Combo meals, Upsizing your meal, Kids menus, Happy hour psychology,
        Tipping screens, Tip creep, Service charges, Loud music and drinking, Music tempo and eating speed,
        Dim lights in restaurants, Fast food value menus, App only deals, Delivery app markups, Ghost kitchens,
        Portion size growth, Bottomless deals, Buffet economics, The specials board, The chef's recommendation,
        Menu prices without cents, Prix fixe menus, Coffee shop size names, Secret menus, Coffee shop loyalty apps,
        Restaurant gift cards, Tasting menus, The separate dessert menu, Drinks first, Would you like fries with that,
        Reservation fees, Airport food prices, Stadium food prices, Why theaters need snack money,
        Fountain drink markup, Dynamic menu pricing, Pizza size math, Restaurant fees on receipts, The lunch special,
        Huge menus, Limited time menu items, Ordering kiosks upsell, Cocktail markups, Restaurant week deals,
        Brunch economics""",
    "Online shopping and apps": """One click buying, Saved cards, Fake countdown timers, Only two left in stock,
        Someone just bought this, Fake reviews, Sponsored results, Dark patterns, Confirmshaming,
        Pre checked boxes, Free returns psychology, Abandoned cart emails, Waiting for the cart discount,
        Mac users saw pricier hotels, Do flight prices rise when you search, Wish lists, Infinite scroll shopping,
        Live shopping streams, TikTok shop impulse buys, Influencer discount codes, Affiliate links,
        Gamified shopping apps, Temu and Shein psychology, Flash sale apps, Push notifications,
        Free gifts with purchase, Frequently bought together, Personalized recommendations, Recently viewed items,
        Strikethrough prices, What the Amazon's choice badge means, Best seller badges, Returns that cost more,
        Restocking fees, Refurbished deals, In app purchases, Ten percent off for your email, Spin to win pop ups,
        Exit pop ups, Comparison sites that sell, Star rating inflation, Many reviews beat high ratings,
        Product photos versus reality, Buy online pick up in store, Online prices that change during the day,
        Marketplace third party sellers, Dropshipping markups, Resale apps, The free shipping progress bar,
        Subscribe and save, Delivery minimums, Coupon extensions, Online quizzes that sell, Pre order hype,
        You are always in a test, Paying for faster shipping""",
    "Subscriptions loyalty and points": """Free trials that renew, Why cancelling is so hard,
        Gym memberships nobody uses, Streaming price hikes, Subscription creep, Annual plans,
        Points make you spend more, Airline miles lose value, Cashback apps, Coffee punch cards, Status tiers,
        Warehouse club memberships, The Prime effect, Subscription boxes, Software subscriptions, Phone plan tiers,
        Insurance auto renewals, Price lock promises, Introductory rates, Subscriptions you forgot,
        Memberships you keep paying, Family plans, Student discounts that end, Gift subscriptions,
        Auto refill programs, Membership tiers decoy, Hotel loyalty programs, Points that expire,
        Badges and streaks, Birthday rewards, Member only prices, App only prices, If it is free you are the product,
        Cheap first year subscriptions, Gym joining fees, Cancel by phone only, Car features by subscription,
        Printer ink subscriptions, The razor and blades trick, Game passes, Meal kit subscriptions,
        Dating app pricing by age, Fitness app subscriptions, Cloud storage creep, Paying to skip ads,
        Ad tiers in streaming, The password sharing crackdown, Lifetime deals, Pause buttons,
        Retention offers when you cancel, Airlines make money on miles, The endowed progress effect,
        The MoviePass story, Delivery subscriptions, Bundles of subscriptions, What subscriptions really cost""",
    "Sales and discounts": """Black Friday tricks, Cyber Monday tricks, Fake original prices, Compare at prices,
        Made for outlet products, Clearance racks, Sale signs, Limited time offers, Countdown sales,
        Doorbuster deals, January sales, When JCPenney stopped sales, Coupons that expire, Stacking coupons,
        Rebates nobody claims, Gift cards nobody uses, Spend fifty get ten, Buy more save more, Price adjustments,
        Sale emails, Members only sales, Friends and family sales, Last chance sales, Going out of business sales,
        Mattress stores always on sale, Back to school sales, Valentine's day markups, Mother's day flower prices,
        Halloween candy economics, After Christmas returns, Tax free weekends, Price drops right after you buy,
        The thrill of a deal, You did not save money, The you saved line on receipts, Sale fatigue, Bargain bins,
        Deal hunting apps, Price hikes before sales, Sample sales, Warehouse sales, End of season sales,
        The psychology of Christmas shopping, Prime Day deals, Up to seventy percent off, Coupon codes that do not work,
        Early access sales, Mystery discount cards, Secret clearance price codes, Anniversary sales,
        Why some stores are always on sale, Thanksgiving grocery tricks, Beauty gift with purchase,
        Holiday gift sets, Floor models and open box, Store credit instead of refunds""",
    "Your brain on money": """Loss aversion, Mental accounting, The pain of paying, Cards feel like play money,
        Sunk cost fallacy, Present bias, Hedonic adaptation, The endowment effect, The IKEA effect,
        Too many choices, The default effect, Status quo bias, Herd buying, Social comparison,
        Keeping up with the Joneses, Lifestyle creep, The Diderot effect, Retail therapy, The scarcity mindset,
        Money and happiness, Experiences versus things, Windfall money, Tax refunds feel like free money,
        The fresh start effect, The planning fallacy, Overconfidence with money, The framing effect, Zero risk bias,
        Money illusion, You do not remember prices, Impulse buying, Dopamine and shopping, Payday spending,
        The latte factor debate, Small purchases add up, Fear of missing out spending, Status spending, Veblen goods,
        Spending savings feels worse, Money scripts, The marshmallow test today, Shopping when sad, Stress spending,
        Boredom buying, Big bills stay in the wallet, Touching makes you want it, Buyer's remorse,
        Post purchase rationalization, Buying time makes you happier, The deadweight loss of gifts,
        Spending on others makes you happier, How nudges work, Temptation bundling, The peak end rule,
        Confirmation bias with money, Why rich people feel poor""",
    "Cards debt and buy now pay later": """The minimum payment trap, How credit card interest grows,
        Zero percent offers, Balance transfer fees, Credit limit increases, Store cards at checkout,
        Buy now pay later, Pay in four, Late fees, Overdraft fees, Payday loans, Rent to own, Stretched car loans,
        Credit score myths, Checking your own score, Credit utilization, Cash advance fees, Foreign transaction fees,
        Pay in your own currency abroad, ATM fees, Debit versus credit protection, Contactless spending, Phone wallets,
        Who really pays for card rewards, Annual fees, Deferred interest, Debt snowball versus avalanche,
        Small debts first, Debt and stress, Lending money to friends, Co signing a loan, Car title loans, Pawn shops,
        Check cashing fees, Layaway is back, Card minimums at shops, Card surcharges, Zero percent furniture deals,
        Phone financing, Leasing versus buying, APR versus APY, The rule of seventy two,
        Compound interest against you, Paying interest on a burrito, Sign up bonuses, Phantom debt,
        The holiday debt hangover, What Americans owe on cards, The box on your statement, Skip a payment offers,
        Payment app scams, Scams that ask for gift cards, Fake debt collectors, Cash advance apps,
        Credit builder loans, Bank fees nobody reads""",
    "Advertising and influence": """Scarcity marketing, Social proof, Doctors in ads, Influencer marketing,
        Celebrity endorsements, Packaging colors, Slack fill, Product placement, Brand loyalty, Logos you remember,
        Jingles, Sonic logos, Scent marketing, The Gruen transfer, Before and after photos, Testimonials,
        Sneaker drops, Hype and queues, Planned obsolescence, The light bulb cartel, Phone upgrade cycles,
        Fast fashion cycles, Advertising to kids, Free gifts that make you owe, Foot in the door, Door in the face,
        Round up for charity, Made in labels, Greenwashing, Fear based marketing, Nostalgia marketing,
        Unboxing videos, Targeted ads, Why ads follow you, Is your phone listening, Brand mascots,
        Color psychology myths, Slogans that stick, Puffery, The fine print, Asterisks in ads,
        But wait there is more, Infomercial shipping fees, Sponsored content labels, Ads that look like articles,
        Search ads that look like results, Brand collaborations, Quiet luxury, Logo size and price,
        Why logos look the same now, The mere exposure effect, The subliminal advertising hoax, Super Bowl ad prices,
        Invite only hype, Banner blindness, Ads that make you cry""",
    "Casinos lotteries and games": """No clocks no windows, Casino carpets, Chips instead of cash,
        Free drinks at the tables, Near misses, Losses disguised as wins, Slot machine sounds, The house edge,
        Players clubs, Casino maze layouts, Lottery odds, What happens to lottery winners, Scratch cards,
        Jackpot fever, Sports betting apps, Free bets that are not free, Parlays, Live betting, Loot boxes,
        Gacha games, Gems hide real prices, Battle passes, Limited time skins, Daily login rewards, Pay to win,
        Whales in mobile games, Claw machines, Arcade tickets, Carnival games, Raffles, Penny slots are not cheap,
        The gambler's fallacy, The hot hand, The illusion of control, Lucky numbers, Sweepstakes,
        The McDonald's Monopoly fraud, Fantasy sports, Streamers and gambling, Skin gambling, Bingo halls,
        Horse racing odds, How betting odds work, Free spins, Bonus rollover rules, The green zero,
        Card counting myths, The martingale trap, Chasing losses, Gambling ads everywhere,
        Who buys lottery tickets, Mystery boxes, Trading card packs, Blind box toys, Prediction markets,
        Variable rewards""",
    "Travel cars and big purchases": """Seat selection fees, Basic economy, Baggage fees, Hidden city tickets,
        The best day to book myth, Hotel minibars, Airport shops, Travel insurance upsells, Rental car upsells,
        Rental car fuel options, Currency exchange booths, Cruise pricing, All inclusive math,
        Timeshare presentations, The four square worksheet, Dealer add ons, Extended warranties,
        The monthly payment trick, Trade in tricks, New car depreciation, Leasing math, Gap insurance upsells,
        Mattress names that change by store, The wedding markup, Three months salary for a ring,
        A diamond is forever, Funeral costs, Home staging, Words in house listings, Home warranties, TV size upsells,
        Summer flight prices, Theme park pricing, Skip the line passes, Home gym equipment nobody uses,
        Luxury watch waitlists, Sneaker resale, Pet costs, Baby product markups, The pink tax, Textbook prices,
        Concert VIP packages, Moving company scams, Car repair upsells, Dealer financing markups,
        Certified pre owned, Car colors and resale, Hotel booking sites, Vacation rental fees, Duty free shopping,
        Tourist trap restaurants, Overbooked flights, Phone roaming charges, The emotional house purchase,
        The IKEA maze, Warranty registration cards""",
    "Money habits that beat the tricks": """The twenty four hour rule, The thirty day list, Shopping lists,
        Cash envelopes, Always check the unit price, Unsubscribe from store emails, Delete your saved cards,
        Turn off one click, Shop alone, Cost per use, Price it in hours of work, Price tracking tools,
        Cancel the trial today, Set reminders for trials, Audit your subscriptions, The no spend challenge,
        The no buy month, Meal planning, Lunch from home math, Coffee at home math, Pay yourself first,
        Automatic savings, Round up savings apps, Separate accounts for goals, Name your savings account,
        The emergency fund, Sinking funds, The fifty thirty twenty budget, Zero based budgeting,
        Track every dollar for a week, Talk about money with friends, Gift budgets, Buy used first,
        Repair before you replace, The library is free, Borrow do not buy, Sell what you do not use,
        Negotiate your bills, Ask for a discount, Check your receipt, Read the cancellation terms, Fun money in cash,
        Pause before you pay, Ask why you want it, Wants versus needs, One in one out, Unfollow to spend less,
        Social media and spending, Generic medicines, The store brand test, Buy in bulk wisely,
        Your free credit report, Celebrate your savings, Make spending harder, Leave your card at home,
        Write down every impulse""",
    "Money history and strange facts": """Why we have price tags, The first credit card, The first coupon,
        The first loyalty stamps, The first supermarket, Nobody wanted shopping carts, The first barcode,
        Why the dollar sign looks like that, Coca Cola cost five cents for seventy years, The end of the penny,
        The first paper money, Hyperinflation stories, How inflation works, The Big Mac index, The lipstick effect,
        Where Black Friday got its name, Where Cyber Monday came from, The first gift card, Christmas club accounts,
        The Sears catalog, The history of tipping, Money superstitions, Lucky pennies, The first dollar stores,
        The five and dime, Monopoly was a warning, Ramen as prison money, Stone money of Yap, Cigarettes as money,
        Shells as money, Why gold is money, The day the dollar left gold, The birth of the credit score,
        The first ATM, Movie ticket prices over time, Fat finger trades, The Pepsi points jet,
        The Hoover free flights fiasco, Tulip mania myths, The South Sea bubble, The dot com crash, Ration books,
        Why ATMs give twenties, How long a dollar bill lasts, The Al Capone laundry myth, The most valuable coin,
        The first vending machine, The first shopping mall, The first online purchase,
        The coin shortage of twenty twenty, The richest person in history, Bank runs,
        How department stores invented browsing, The first money back guarantee, Famous price wars,
        Why a dollar is called a buck""",
}

MONTH_1 = """The middle size trap, Why the milk is at the back, Losses disguised as wins, Cards feel like play money,
    Fake countdown timers, The minimum payment trap, Menus without dollar signs, Free trials that renew,
    Made for outlet products, The four square worksheet, Nobody wanted shopping carts, Slack fill,
    Price it in hours of work, Store brands made by big brands, Why prices end in ninety nine,
    The second cheapest wine, Only two left in stock, Coffee punch cards, The IKEA effect, Buy now pay later,
    Near misses, A diamond is forever, The Pepsi points jet, Planned obsolescence, The twenty four hour rule,
    Shrinkflation, Drip pricing, Tipping screens, Mac users saw pricier hotels, Points make you spend more,
    Rebates nobody claims, The pain of paying, Deferred interest, Is your phone listening, Chips instead of cash,
    The wedding markup, Cost per use, The Hoover free flights fiasco, Eye level is buy level,
    Why expensive wine tastes better, Loud music and drinking, Dark patterns, Car features by subscription,
    When JCPenney stopped sales, The Diderot effect, Pay in your own currency abroad, The Gruen transfer,
    Loot boxes, Timeshare presentations, Cash envelopes, Coca Cola cost five cents for seventy years,
    The checkout candy trap, The rule of one hundred, Delivery app markups, Free returns psychology,
    Why cancelling is so hard, Fake original prices, Money and happiness, Phantom debt, The light bulb cartel"""

# dated topics: slug -> day (moved to the morning slot of that day)
SEASONAL = {
    "thanksgiving-grocery-tricks": "2026-11-26",
    "black-friday-tricks": "2026-11-27",
    "where-black-friday-got-its-name": "2026-11-28",
    "cyber-monday-tricks": "2026-11-30",
    "the-psychology-of-christmas-shopping": "2026-12-12",
    "gift-cards-nobody-uses": "2026-12-19",
    "after-christmas-returns": "2026-12-26",
    "the-fresh-start-effect": "2027-01-01",
    "gym-memberships-nobody-uses": "2027-01-04",
    "the-holiday-debt-hangover": "2027-01-10",
    "valentines-day-markups": "2027-02-14",
    "tax-refunds-feel-like-free-money": "2027-04-15",  # US tax day
    "mothers-day-flower-prices": "2027-05-09",  # US Mother's Day
    "summer-flight-prices": "2027-06-01",
    "back-to-school-sales": "2027-08-01",
    "tax-free-weekends": "2027-08-06",
    "halloween-candy-economics": "2027-10-31",
}


def split(text):
    return [t.strip() for t in text.replace("\n", " ").split(",") if t.strip()]


def slug(title):
    return re.sub(r"[^a-z0-9]+", "-", title.lower().replace("'", "")).strip("-")


def main():
    category_of, problems = {}, []
    for category, text in CATEGORIES.items():
        for title in split(text):
            if slug(title) in category_of:
                problems.append(f"duplicate: {title}")
            category_of[slug(title)] = (category, title)
    counts = {c: len(split(t)) for c, t in CATEGORIES.items()}
    if len(category_of) != 730:
        problems.append(f"{len(category_of)} topics in total, expected 730 ({counts})")

    month_1 = [slug(t) for t in split(MONTH_1)]
    problems += [f"month 1 topic not in a category: {s}" for s in month_1 if s not in category_of]
    problems += [f"month 1 topic has a date: {s}" for s in month_1 if s in SEASONAL]
    problems += [f"dated topic not in a category: {s}" for s in SEASONAL if s not in category_of]
    if len(set(month_1)) != 60:
        problems.append(f"month 1 has {len(set(month_1))} different topics, expected 60")
    if problems:
        sys.exit("\n".join(problems))

    # spread the rest evenly: item k of a category with n items sits at position (k + 0.5) / n
    rest = []
    for category, text in CATEGORIES.items():
        items = [slug(t) for t in split(text) if slug(t) not in month_1 and slug(t) not in SEASONAL]
        rest += [((k + 0.5) / len(items), category, s) for k, s in enumerate(items)]
    order = month_1 + [s for _, _, s in sorted(rest)]

    # then each dated topic goes in the morning slot of its date (evening if the morning is taken)
    wanted = {}
    for s, day in SEASONAL.items():
        i = (date.fromisoformat(day) - START).days * 2
        while i in wanted:
            i += 1
        wanted[i] = s
    for i in sorted(wanted):
        order.insert(i, wanted[i])

    plan = []
    for i, s in enumerate(order):
        category, title = category_of[s]
        plan.append({"n": i + 1, "date": str(START + timedelta(days=i // 2)), "time": SLOTS[i % 2],
                     "id": s, "category": category, "title": title})
    save_json(ROOT / "topic_plan.json", plan)
    print(f"{len(plan)} topics, {plan[0]['date']} -> {plan[-1]['date']}")
    print("per category: " + ", ".join(f"{c} {n}" for c, n in counts.items()))


if __name__ == "__main__":
    main()
