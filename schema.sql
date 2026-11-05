CREATE TABLE IF NOT EXISTS books (id SERIAL PRIMARY KEY,title TEXT NOT NULL,author TEXT NOT NULL,genre TEXT,file_path TEXT,file_id TEXT,text_content TEXT);
CREATE TABLE IF NOT EXISTS user_books (user_id BIGINT NOT NULL,book_id INT NOT NULL REFERENCES books(id) ON DELETE CASCADE,is_favorite BOOLEAN DEFAULT FALSE,last_page INT DEFAULT 1,last_opened_at TIMESTAMPTZ,created_at TIMESTAMPTZ DEFAULT NOW(),PRIMARY KEY(user_id,book_id));
CREATE TABLE IF NOT EXISTS audio_jobs (id SERIAL PRIMARY KEY,user_id BIGINT NOT NULL,book_id INT NOT NULL REFERENCES books(id) ON DELETE CASCADE,status TEXT NOT NULL DEFAULT 'pending',chunk_index INT NOT NULL DEFAULT 0,total_chunks INT,telegram_file_id TEXT,error TEXT,created_at TIMESTAMPTZ DEFAULT NOW(),updated_at TIMESTAMPTZ DEFAULT NOW());
CREATE TABLE IF NOT EXISTS audio_chunks (job_id INT REFERENCES audio_jobs(id) ON DELETE CASCADE,chunk_index INT NOT NULL,text_content TEXT NOT NULL,telegram_file_id TEXT,PRIMARY KEY(job_id,chunk_index));
CREATE INDEX IF NOT EXISTS idx_user_books_recent ON user_books(user_id,last_opened_at DESC NULLS LAST); CREATE INDEX IF NOT EXISTS idx_user_books_fav ON user_books(user_id,is_favorite) WHERE is_favorite=TRUE; CREATE INDEX IF NOT EXISTS idx_audio_jobs_status ON audio_jobs(status,created_at);
ALTER TABLE audio_jobs ADD COLUMN IF NOT EXISTS attempts INT NOT NULL DEFAULT 0;
ALTER TABLE audio_jobs ADD COLUMN IF NOT EXISTS max_attempts INT NOT NULL DEFAULT 3;
CREATE TABLE IF NOT EXISTS book_chapters (id SERIAL PRIMARY KEY,book_id INT NOT NULL REFERENCES books(id) ON DELETE CASCADE,title TEXT NOT NULL,chapter_no INT NOT NULL,content TEXT NOT NULL,UNIQUE(book_id,chapter_no));
CREATE TABLE IF NOT EXISTS book_pages (id SERIAL PRIMARY KEY,book_id INT NOT NULL REFERENCES books(id) ON DELETE CASCADE,page_no INT NOT NULL,content TEXT NOT NULL,UNIQUE(book_id,page_no));
ALTER TABLE audio_chunks ADD COLUMN IF NOT EXISTS status TEXT NOT NULL DEFAULT 'pending';
ALTER TABLE audio_chunks ADD COLUMN IF NOT EXISTS attempts INT NOT NULL DEFAULT 0;
CREATE INDEX IF NOT EXISTS idx_book_pages_book ON book_pages(book_id,page_no);
CREATE INDEX IF NOT EXISTS idx_chapters_book ON book_chapters(book_id,chapter_no);
INSERT INTO books(title,author) VALUES ('Война и мир','Лев Толстой'),('Братья Карамазовы','Федор Достоевский'),('Как закалялась сталь','Николай Островский') ON CONFLICT DO NOTHING;

