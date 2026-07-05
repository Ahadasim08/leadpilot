create extension if not exists vector;

create table documents (
  id uuid primary key default gen_random_uuid(),
  filename text not null,
  file_type text not null,
  created_at timestamptz default now()
);

create table chunks (
  id uuid primary key default gen_random_uuid(),
  document_id uuid references documents(id) on delete cascade,
  content text not null,
  chunk_index int not null,
  embedding vector(384)
);
-- HNSW index — accurate at all scales, no tuning needed
create index on chunks using hnsw (embedding vector_cosine_ops);

create or replace function match_chunks(
  query_embedding vector(384), match_count int, similarity_threshold float)
returns table (id uuid, document_id uuid, filename text, content text, similarity float)
language plpgsql stable as $$
begin
  -- Force sequential scan so small datasets are never missed by the index
  set local enable_indexscan = off;
  return query
    select c.id, c.document_id, d.filename, c.content,
           1 - (c.embedding <=> query_embedding) as similarity
    from chunks c
    join documents d on d.id = c.document_id
    where 1 - (c.embedding <=> query_embedding) >= similarity_threshold
    order by c.embedding <=> query_embedding
    limit match_count;
end;
$$;
