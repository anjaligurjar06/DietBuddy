# DietBuddy Backend

DietBuddy backend is a FastAPI service that connects the React frontend to Supabase and OpenRouter AI. It manages user profile data, daily meal logs, food tracker entries, macro estimates, and diet-aware food recommendations.

## What The Backend Does

- Saves profile details such as age, height, weight, goal, activity, allergies, and diet type.
- Saves daily diet logs: breakfast, lunch, dinner, and snacks.
- Saves individual food tracker entries with calories and macros.
- Estimates nutrition values for foods using AI.
- Generates food recommendations using today's meals, tracked foods, profile data, and diet preference.
- Enforces diet preference rules so vegetarian and vegan users do not receive invalid recommendations.
- Provides local fallback recommendations if OpenRouter is unavailable or rate-limited.

## Requirements

Install these Python dependencies from `requirements.txt`:

```text
fastapi
uvicorn
supabase
requests
pydantic
python-dotenv
PyJWT
httpx
```

You also need:

- Python virtual environment
- Supabase project
- Supabase public tables
- OpenRouter API key for AI recommendations and nutrition estimates

## Setup

From the project root:

```powershell
cd backend
..\Venv\Scripts\activate
pip install -r requirements.txt
```

Create `backend/.env`:

```env
SUPABASE_URL=your_supabase_project_url
SUPABASE_KEY=your_supabase_key
OPENROUTER_API_KEY=your_openrouter_key
AI_MODEL=meta-llama/llama-3-8b-instruct
JWT_SECRET=change-this-secret
```

Do not commit real keys.

## Run The Backend

```powershell
cd backend
uvicorn app.main:app --reload
```

Backend runs at:

```text
http://127.0.0.1:8000
```

Interactive API docs:

```text
http://127.0.0.1:8000/docs
```

## Environment Notes

The backend removes broken proxy environment variables before calling Supabase/OpenRouter:

```text
HTTP_PROXY
HTTPS_PROXY
ALL_PROXY
```

This is needed because a dead local proxy can stop Python from reaching Supabase or OpenRouter.

## Supabase Tables

### `public.users`

Stores app profile details. Supabase Auth handles login, but this table stores DietBuddy-specific profile data.

Recommended columns:

```text
id uuid primary key
age int
gender text
height float8
weight float8
goal text
health text
allergies text
diet text
activity text
```

Important:

```text
public.users.id must match the Supabase Auth user id.
```

### `public.diet_entries`

Stores daily meal text from the diet page.

Recommended columns:

```text
id uuid primary key
user_id uuid
breakfast text
lunch text
dinner text
snacks text
created_at timestamp default now()
```

### `public.food_entries`

Stores food tracker entries and macro estimates.

Recommended columns:

```text
id uuid primary key
user_id uuid
food_name text
grams numeric
created_at timestamp default now()
calories float8
protein float8
carbs float8
fats float8
```

## Authentication

The frontend authenticates users with Supabase Auth.

For protected routes, the frontend sends:

```http
Authorization: Bearer <supabase_access_token>
```

The backend uses that token to:

- confirm the Supabase user id
- make sure users cannot write data for another user
- save/query data under the correct `user_id`

## API Endpoints

### Health Check

```http
GET /
```

Returns:

```json
{
  "message": "Welcome to the Diet and Food API!"
}
```

## Auth/Profile APIs

### Save Profile

```http
POST /auth/profile
```

Requires:

```http
Authorization: Bearer <supabase_access_token>
```

Request body:

```json
{
  "user_id": "auth-user-uuid",
  "name": "Anish",
  "age": 22,
  "gender": "Male",
  "height": 175,
  "weight": 70,
  "goal": "Gain Weight",
  "health": "no issues",
  "allergies": "none",
  "diet": "Vegetarian",
  "activity": "Moderate"
}
```

What it does:

- Verifies the token belongs to `user_id`.
- Saves profile data into `public.users`.
- Supports schemas that use `id` as the user id column.
- The frontend also stores profile data in Supabase Auth metadata during signup.

### Get Profile

```http
GET /auth/profile/{user_id}
```

Optional:

```http
Authorization: Bearer <supabase_access_token>
```

What it does:

- Looks for the profile in `public.users`.
- If no row exists, falls back to Supabase Auth metadata.
- If metadata is missing too, returns safe default values.

Used by:

- Dashboard calorie budget
- BMI calculation
- diet preference selector
- recommendations

## Diet APIs

### Save Daily Diet

```http
POST /diet/add
```

Requires:

```http
Authorization: Bearer <supabase_access_token>
```

Request body:

```json
{
  "user_id": "auth-user-uuid",
  "breakfast": "oats and banana",
  "lunch": "rice and dal",
  "dinner": "paneer wrap",
  "snacks": "fruit"
}
```

What it does:

- Verifies the logged-in Supabase user.
- Inserts a row into `public.diet_entries`.
- Stores meals for the current date/time.

### Get Diet Entries By User

```http
GET /diet/{user_id}
```

Returns all diet entries for a user.

Used by the login flow to decide whether a user should go to:

- `/diet` for new users
- `/dashboard` for users with diet history

### Get Today's Diet

```http
GET /diet/today
```

Requires local JWT auth from the older backend auth helper.

Returns today's diet entry for the authenticated user.

### Get Diet History

```http
GET /diet/history
```

Requires local JWT auth from the older backend auth helper.

Returns recent diet entries.

### Update Diet Entry

```http
PUT /diet/entry/{entry_id}
```

Updates breakfast, lunch, dinner, or snacks for an entry owned by the authenticated user.

### Delete Diet Entry

```http
DELETE /diet/entry/{entry_id}
```

Deletes an entry owned by the authenticated user.

## Food Tracker APIs

### Add Food

```http
POST /food/add
```

Optional but recommended:

```http
Authorization: Bearer <supabase_access_token>
```

Request body:

```json
{
  "user_id": "auth-user-uuid",
  "food_name": "rice",
  "grams": 100
}
```

What it does:

- Verifies token ownership if a token is provided.
- Sends the food name and grams to the AI nutrition helper.
- Receives estimated calories, protein, carbs, and fats.
- Inserts the final row into `public.food_entries`.

Example response:

```json
{
  "message": "Food entry added to database",
  "data": [
    {
      "id": "entry-uuid",
      "user_id": "auth-user-uuid",
      "food_name": "rice",
      "grams": 100,
      "calories": 364,
      "protein": 6,
      "carbs": 82,
      "fats": 2
    }
  ]
}
```

### Get Foods By User

```http
GET /food/{user_id}
```

Optional but recommended:

```http
Authorization: Bearer <supabase_access_token>
```

Returns tracked foods for the user.

The frontend filters these entries to today's date for:

- daily calories
- macro chart
- daily budget bar
- daily food log

### Get Food Recommendations

```http
GET /food/recommendations/{user_id}
```

Optional but recommended:

```http
Authorization: Bearer <supabase_access_token>
```

What it uses:

- user profile from `public.users`
- Supabase Auth metadata fallback
- diet preference: Vegetarian, Non-Vegetarian, Vegan
- today's `diet_entries`
- today's `food_entries`
- today's macro totals
- allergies and health notes

What it returns:

```json
{
  "message": "Recommendations generated successfully",
  "diet": "Vegetarian",
  "recommendation_source": "ai",
  "warning": null,
  "based_on": {
    "meals": {
      "breakfast": "pizza",
      "lunch": "rice and dal",
      "dinner": "rajma",
      "snacks": "fruit"
    },
    "totals": {
      "calories": 742,
      "protein": 14,
      "carbs": 166,
      "fats": 3
    },
    "foods_logged": 2
  },
  "data": [
    {
      "id": 1,
      "food_name": "Lentil Soup",
      "calories": 116,
      "protein": 9,
      "carbs": 20,
      "fats": 1,
      "reason": "Adds plant protein while keeping calories moderate."
    }
  ]
}
```

Diet enforcement:

- Vegetarian users never receive meat, chicken, fish, seafood, or eggs.
- Vegan users never receive meat, eggs, dairy, paneer, curd, yogurt, cheese, ghee, or honey.
- If AI suggests an invalid food, the backend removes it before responding.
- If fewer than 5 AI recommendations survive filtering, local safe recommendations fill the gap.

Fallback behavior:

- If OpenRouter fails, returns local recommendations.
- Response includes:

```json
{
  "recommendation_source": "local_fallback",
  "warning": "Using local recommendations because AI recommendations are temporarily unavailable."
}
```

## AI Helpers

Located in:

```text
app/utils/ai_nutrition.py
```

Main functions:

- `get_nutrition(food_name, grams)` estimates calories/macros for food tracker entries.
- `get_food_recommendations(context)` asks OpenRouter for recommendation JSON.
- `analyze_meals(meals)` returns a text-based nutrition analysis.
- `suggest_meal_plan(...)` creates a one-day meal plan.

The AI recommendation parser:

- requests JSON mode
- ignores model-provided ids
- assigns backend numeric ids
- repairs malformed JSON when possible

## How The Main App Flow Works

1. User signs up or logs in with Supabase Auth.
2. Signup profile details are sent to `/auth/profile`.
3. Profile details are stored in `public.users`.
4. User logs meals on `/diet`.
5. `/diet/add` stores meal text in `diet_entries`.
6. User tracks foods on dashboard.
7. `/food/add` estimates macros and stores entries in `food_entries`.
8. Dashboard fetches profile, food entries, and recommendations.
9. Recommendations are generated from profile + today's meals + today's foods.
10. Frontend displays BMI-based daily calorie budget and macro chart.

## Troubleshooting

### Profile details are missing

Check `public.users`.

The current authenticated user id must have a matching row:

```text
public.users.id = auth.users.id
```

If a profile row is missing, the backend falls back to Supabase Auth metadata or safe defaults.

### Recommendations show local fallback

Possible reasons:

- OpenRouter is rate-limited.
- OpenRouter API key is missing or invalid.
- AI model returned malformed JSON that could not be repaired.

### Supabase insert fails with RLS

Make sure policies allow users to insert/select their own rows.

Example for `food_entries`:

```sql
create policy "Users can insert own food entries"
on public.food_entries
for insert
to authenticated
with check (auth.uid() = user_id);

create policy "Users can read own food entries"
on public.food_entries
for select
to authenticated
using (auth.uid() = user_id);
```

Example for `diet_entries`:

```sql
create policy "Users can insert own diet entries"
on public.diet_entries
for insert
to authenticated
with check (auth.uid() = user_id);

create policy "Users can read own diet entries"
on public.diet_entries
for select
to authenticated
using (auth.uid() = user_id);
```

### Backend cannot connect to Supabase or OpenRouter

The app removes broken proxy variables in code, but also check your terminal environment for:

```text
HTTP_PROXY
HTTPS_PROXY
ALL_PROXY
```

### OpenRouter returns 429

The selected model is rate-limited upstream. Try again later or set a different `AI_MODEL` in `.env`.

## Development Checks

Compile backend:

```powershell
cd backend
..\Venv\Scripts\python.exe -m compileall app
```

Run frontend build from the frontend folder:

```powershell
npm run build
```
