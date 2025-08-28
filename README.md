# Rent-a-prop

Amarketplace platform for cosplayers for buying, selling, and renting anime props and collectibles. Built with Streamlit and Supabase.

## Features

- **User Authentication**: Email/password and Google OAuth signup/signin
- **Listings Management**: Create, browse, and manage anime prop listings
- **Direct Messaging**: Chat between buyers and sellers
- **AI-Powered Features**: 
  - AI-generated listing descriptions
  - Auto-tagging for better discovery
  - Franchise detection from descriptions
- **Mobile-Friendly Design**: Responsive layout optimized for all devices

## Tech Stack

- **Frontend**: Streamlit
- **Backend**: Supabase (Auth, Database, Storage)
- **AI Services**: Hugging Face Inference API
- **Deployment**: Streamlit Community Cloud

## Setup Instructions

### Prerequisites

- Python 3.8+
- Supabase account
- Hugging Face account (for AI features)

### Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd anime-prop-marketplace
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up environment variables:
   - Create a `.streamlit/secrets.toml` file with your credentials:

```toml
[supabase]
url = "https://your-project.supabase.co"
anon_key = "your-anon-key"
redirect_url = "https://your-streamlit-app-url"

HF_TOKEN = "hf_your-huggingface-token"
```

4. Set up Supabase:
   - Create a new project in Supabase
   - Enable Google OAuth in the Auth providers section
   - Run the SQL schema to create necessary tables (see `schema.sql`)

5. Run the application:
```bash
streamlit run streamlit_app.py
```

## Database Schema

The application uses the following tables in Supabase:

### Profiles
- `id` (UUID, primary key)
- `display_name` (text)
- `city` (text)
- `bio` (text)
- `role_flags` (integer)
- `upi_id` (text)
- `avatar_url` (text)
- `created_at` (timestamp)

### Listings
- `id` (UUID, primary key)
- `owner` (UUID, foreign key to profiles)
- `ltype` (text: 'rent', 'sell', 'commission')
- `title` (text)
- `description` (text)
- `price` (numeric)
- `price_unit` (text: 'day', 'fixed')
- `city` (text)
- `franchise` (text)
- `character` (text)
- `handmade` (boolean)
- `source` (text: 'handmade', 'bought')
- `tags` (text[])
- `images` (text[])
- `quantity` (integer)
- `status` (text: 'active', 'sold_out', 'paused')
- `created_at` (timestamp)

### Chats
- `id` (UUID, primary key)
- `listing` (UUID, foreign key to listings)
- `buyer` (UUID, foreign key to profiles)
- `seller` (UUID, foreign key to profiles)
- `last_msg` (timestamp)
- `updated_at` (timestamp)

### Messages
- `id` (UUID, primary key)
- `chat` (UUID, foreign key to chats)
- `sender` (UUID, foreign key to profiles)
- `text` (text)
- `created_at` (timestamp)

## AI Features

The application leverages Hugging Face models for:

1. **Write with AI**: Uses `meta-llama/Meta-Llama-3.1-8B-Instruct` to generate listing descriptions
2. **Auto-tagging**: Uses `facebook/bart-large-mnli` for zero-shot classification to suggest tags
3. **Image Captioning**: Uses `Salesforce/blip-image-captioning-base` to generate captions for images
4. **Franchise Detection**: Uses `facebook/bart-large-mnli` to guess franchises from descriptions

## Deployment

1. Push your code to a GitHub repository
2. Connect your repository to Streamlit Community Cloud
3. Add your secrets to the Streamlit Cloud settings
4. Deploy the application

## Important Notes

- **Transaction Handling**: This platform does not handle delivery, payment, or escrow services
- **User Responsibility**: Users are responsible for arranging their own transactions safely
- **Rate Limits**: The free tier of Hugging Face API has rate limits

## Support

For issues and questions, please check the documentation or create an issue in the repository.

## License

This project is licensed under the MIT License.
