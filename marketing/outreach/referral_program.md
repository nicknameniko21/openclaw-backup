# Referral Program Design

## Program Overview

**Program Name:** Share the Success

**Tagline:** "Give free verifications, get free verifications. It's that simple."

**Core Concept:** Dropbox-style incentivized referrals where both the referrer and referee receive immediate, tangible value tied directly to the product.

---

## Program Structure

### AI Identity Pro Rewards

#### Referrer Rewards (The Sender)

| Tier | Referrals Made | Reward |
|------|----------------|--------|
| Starter | 1st referral | 50 free verifications |
| Regular | 2-4 referrals | 50 free verifications each |
| Advocate | 5-9 referrals | 75 free verifications each + "Advocate" badge |
| Champion | 10-24 referrals | 100 free verifications each + priority support |
| Legend | 25+ referrals | 150 free verifications each + annual conference ticket |

**Additional Milestone Bonuses:**
- 5 referrals: $100 account credit
- 10 referrals: 1 month free (any plan)
- 25 referrals: Lifetime 20% discount
- 50 referrals: Lifetime free Pro account

#### Referee Rewards (The Recipient)

| Action | Reward |
|--------|--------|
| Sign up via referral link | 25 free verifications |
| Complete first verification | Additional 25 free verifications |
| Upgrade to paid plan | 1 month free on their plan |

### Meetily Pro Rewards

#### Referrer Rewards (The Sender)

| Tier | Referrals Made | Reward |
|------|----------------|--------|
| Starter | 1st referral | 1 month free |
| Regular | 2-4 referrals | 1 month free each |
| Advocate | 5-9 referrals | 2 months free each + "Advocate" badge |
| Champion | 10-24 referrals | 3 months free each + priority support |
| Legend | 25+ referrals | 6 months free each + annual conference ticket |

**Additional Milestone Bonuses:**
- 5 referrals: $50 account credit
- 10 referrals: 6 months free
- 25 referrals: Lifetime 25% discount
- 50 referrals: Lifetime free Business plan

#### Referee Rewards (The Recipient)

| Action | Reward |
|--------|--------|
| Sign up via referral link | 50% off first month |
| Complete first meeting | Additional 50% off second month |
| Upgrade to annual plan | 2 months free |

---

## Tracking Mechanism

### Technical Implementation

**Referral Link Structure:**
```
https://aiidentitypro.com/?ref=USER123
https://meetilypro.com/?ref=USER456
```

**Tracking Flow:**
1. User shares unique referral link
2. Referee clicks link → cookie set (60-day duration)
3. Referee signs up → referral attributed to referrer
4. Referee completes qualifying action → rewards unlocked
5. Both parties notified → rewards applied automatically

**Database Schema:**
```sql
referrals:
- id (uuid)
- referrer_user_id (foreign key)
- referee_user_id (foreign key, nullable)
- referral_code (unique string)
- status (pending/converted/expired)
- created_at (timestamp)
- converted_at (timestamp)
- reward_claimed (boolean)

referral_rewards:
- id (uuid)
- user_id (foreign key)
- referral_id (foreign key)
- reward_type (credits/months/credit)
- reward_amount
- status (pending/applied/expired)
- applied_at (timestamp)
```

### Dashboard Design

**Referrer Dashboard Elements:**

```
┌─────────────────────────────────────────────────────┐
│  YOUR REFERRALS                                     │
├─────────────────────────────────────────────────────┤
│                                                     │
│  [Share Button] [Copy Link] [Email] [Social]       │
│                                                     │
│  Your link: https://aiidentitypro.com/?ref=ABC123  │
│                                                     │
├─────────────────────────────────────────────────────┤
│  PROGRESS TO NEXT REWARD                            │
├─────────────────────────────────────────────────────┤
│                                                     │
│  Current Tier: Advocate (7 referrals)              │
│  Next Tier: Champion (10 referrals)                │
│                                                     │
│  [████████░░░░░░░░░░] 7/10                         │
│                                                     │
│  3 more referrals = Champion status!               │
│  Reward: 100 free verifications each + priority    │
│                                                     │
├─────────────────────────────────────────────────────┤
│  YOUR STATS                                         │
├─────────────────────────────────────────────────────┤
│                                                     │
│  Total Referrals: 7                                │
│  Successful Conversions: 5                         │
│  Rewards Earned: 325 free verifications            │
│  Pending Rewards: 50 free verifications            │
│                                                     │
├─────────────────────────────────────────────────────┤
│  REFERRAL HISTORY                                   │
├─────────────────────────────────────────────────────┤
│                                                     │
│  [Table showing each referral status]              │
│  Name    | Status      | Reward      | Date        │
│  ────────┼─────────────┼─────────────┼─────────────│
│  John D. | Converted   | 50 credits  | Jan 15      │
│  Sarah M.| Pending     | -           | Jan 18      │
│  ...                                                │
│                                                     │
└─────────────────────────────────────────────────────┘
```

---

## Landing Page Copy

### Hero Section

**Headline:**
```
Share AI Identity Pro,
Get Free Verifications
```

**Subheadline:**
```
Give your friends 50 free verifications.
Get 50 free verifications for each friend who signs up.
It's a win-win.
```

**CTA:**
```
[Start Referring - It's Free]
```

### How It Works Section

**Section Title:** How Referrals Work

**Step 1:**
```
📤 Share Your Link
Copy your unique referral link and share it with friends, colleagues, or your network.
```

**Step 2:**
```
🎁 They Sign Up
Your friends get 25 free verifications just for signing up with your link.
```

**Step 3:**
```
🎉 You Both Win
When they complete their first verification, you get 50 free verifications added to your account.
```

### Rewards Section

**Section Title:** The More You Share, The More You Earn

**Cards:**

```
┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
│   1 FRIEND      │  │   5 FRIENDS     │  │   10 FRIENDS    │
│                 │  │                 │  │                 │
│   50 credits    │  │   375 credits   │  │   1,000 credits │
│   + $0 bonus    │  │   + $100 bonus  │  │   + 1 month free│
│                 │  │                 │  │                 │
│   [Get Started] │  │   [Get Started] │  │   [Get Started] │
└─────────────────┘  └─────────────────┘  └─────────────────┘
```

### Social Proof Section

**Section Title:** Join Thousands of Happy Referrers

**Testimonials:**

```
"I've earned over 2,000 free verifications just by sharing 
with my network. The program literally pays for itself."
— Jennifer K., Compliance Manager

"Referred my entire team. Now we're all saving money and 
our verification process is bulletproof."
— Marcus T., CTO

"The referral program helped us scale without increasing 
our budget. Best referral program I've seen."
— Sarah L., Operations Director
```

**Stats:**
```
10,000+ active referrers
500,000+ verifications earned
$2M+ in rewards given
```

### FAQ Section

**Q: Is there a limit to how many people I can refer?**
A: Nope! Refer as many people as you want. There's no cap on your earnings.

**Q: When do I get my rewards?**
A: Rewards are added to your account instantly when your referral completes their first verification.

**Q: Do my free verifications expire?**
A: No, your earned verifications never expire. Use them whenever you need.

**Q: Can I refer people who already have an account?**
A: Referrals are for new customers only. They must sign up using your unique referral link.

**Q: What if my referral cancels their account?**
A: You keep your earned rewards regardless of what your referral does after signing up.

### Final CTA Section

**Headline:**
```
Start Earning Free Verifications Today
```

**Subheadline:**
```
It takes 30 seconds to get your referral link.
Your first 50 free verifications are waiting.
```

**CTA:**
```
[Get My Referral Link]
```

**Secondary CTA:**
```
[See Full Program Details]
```

---

## Email Templates

### Referral Invitation Email (Sent by Referrer)

**Subject:** I thought you'd find this useful

**Body:**
```
Hey [Friend's Name],

I've been using AI Identity Pro for identity verification and it's been a game-changer for us.

• Verification time: 3 days → 5 seconds
• Fraud caught: Multiple attempts already
• Team time saved: 40+ hours/week

I think it could help [Their Company] too.

If you sign up with my link, you'll get 50 free verifications to try it out:
→ [Referral Link]

Let me know if you have any questions!

[Your Name]
```

### Referral Success Email (To Referrer)

**Subject:** 🎉 You earned 50 free verifications!

**Body:**
```
Hi [Name],

Great news! [Referee Name] just completed their first verification.

Your reward: 50 free verifications have been added to your account.

Current stats:
• Total referrals: [X]
• Successful conversions: [Y]
• Total rewards earned: [Z] verifications
• Next milestone: [Next Reward] at [X] referrals

Keep sharing: [Referral Link]

Thanks for spreading the word!

The [Company] Team
```

### Milestone Achievement Email

**Subject:** 🏆 You've reached [Tier] status!

**Body:**
```
Hi [Name],

Congratulations! You've referred [X] friends to AI Identity Pro.

You've unlocked [Tier] status!

New benefits:
• [Benefit 1]
• [Benefit 2]
• [Benefit 3]

Your next milestone: [Next Tier] at [Y] referrals
Reward: [Next Reward]

You're doing amazing! Keep sharing: [Referral Link]

The [Company] Team
```

---

## Promotion Strategy

### In-App Promotion

**Referral Widget (Dashboard):**
- Persistent but non-intrusive widget
- Shows current referral count
- One-click sharing
- Progress to next milestone

**Post-Action Prompts:**
- After successful verification: "Love AI Identity Pro? Share it!"
- After monthly report: "Know someone who needs this?"
- After upgrade: "Maximize your value—refer friends"

**Settings Page:**
- Dedicated referrals tab
- Full dashboard
- Sharing tools
- History

### Email Campaign

**Onboarding Sequence:**
- Day 1: Welcome (mention referral program)
- Day 7: First success email + referral ask
- Day 14: Referral program highlight
- Day 30: Milestone check-in

**Monthly Newsletter:**
- Top referrers spotlight
- New rewards announcement
- Referral tips

### Social Media

**Organic Posts:**
- Customer referral success stories
- "Referral program explained" video
- Milestone celebrations

**Paid Ads:**
- Target existing customers
- Lookalike audiences
- Retargeting website visitors

---

## Program Rules & Terms

### Eligibility
- Must be an active customer
- Account in good standing
- 14+ days since first purchase (anti-gaming)

### Qualifying Referrals
- New customer only (no existing accounts)
- Must use unique referral link
- Must complete qualifying action within 60 days
- Must not be from same company (for B2B)

### Prohibited Activities
- Self-referrals
- Spam or unsolicited bulk messaging
- Fake accounts
- Misrepresenting the program
- Buying/selling referral codes

### Violation Consequences
- First offense: Warning + forfeiture of suspicious rewards
- Second offense: Program suspension
- Third offense: Account termination

### Changes to Program
- 30-day notice for material changes
- Grandfather existing rewards
- Email notification to all participants

---

## Success Metrics

### Track Weekly:
- Referral link shares
- Clicks on referral links
- Signups from referrals
- Conversion rate (click → signup)
- Rewards distributed

### Track Monthly:
- % of customers who refer
- Average referrals per referrer
- Revenue from referral channel
- CAC via referrals vs other channels
- Referral program NPS

### Goals (First Year):

| Quarter | Active Referrers | Total Referrals | Revenue from Referrals |
|---------|------------------|-----------------|------------------------|
| Q1 | 100 | 200 | $10K |
| Q2 | 300 | 750 | $35K |
| Q3 | 600 | 1,500 | $75K |
| Q4 | 1,000 | 3,000 | $150K |

---

## Meetily Pro Referral Variants

### Landing Page Differences

**Hero Headline:**
```
Share Smarter Meetings,
Get Free Months
```

**Subheadline:**
```
Give your friends 50% off their first month.
Get 1 month free for each friend who subscribes.
```

**Rewards Cards:**
```
┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
│   1 FRIEND      │  │   5 FRIENDS     │  │   10 FRIENDS    │
│                 │  │                 │  │                 │
│   1 month free  │  │   7 months free │  │   16 months free│
│   + $0 bonus    │  │   + $50 bonus   │  │   + 6 mo free   │
│                 │  │                 │  │                 │
│   [Get Started] │  │   [Get Started] │  │   [Get Started] │
└─────────────────┘  └─────────────────┘  └─────────────────┘
```

### Email Subject Line Variants

- "Free months are waiting for you"
- "Your friends save 50%, you get free months"
- "The easiest way to get free Meetily Pro"
- "Share smarter meetings, get rewarded"
