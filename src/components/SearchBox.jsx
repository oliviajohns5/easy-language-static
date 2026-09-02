import { useMemo, useState } from 'react';

export default function SearchBox({ pages }) {
  const [query, setQuery] = useState('');
  const results = useMemo(() => {
    const q = query.trim().toLowerCase();
    if (!q) return [];
    return pages.filter((page) => `${page.title} ${page.description}`.toLowerCase().includes(q)).slice(0, 7);
  }, [query, pages]);

  return (
    <section className="panel search-panel">
      <h2>Поиск</h2>
      <input value={query} onChange={(e) => setQuery(e.target.value)} placeholder="Найти курс…" aria-label="Поиск по сайту" />
      {results.length > 0 && (
        <ul className="search-results">
          {results.map((page) => <li key={page.path}><a href={page.path}>{page.title}</a><p>{page.description}</p></li>)}
        </ul>
      )}
    </section>
  );
}
