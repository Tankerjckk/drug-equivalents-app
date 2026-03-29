"use client";

import Image from "next/image";
import { useEffect, useRef, useState } from "react";
import { API_URL } from "../lib/api";

type SearchItem = {
  id: number;
  brand_name: string;
  common_name: string;
  active_substance_raw: string;
  strength_raw: string;
  pharmaceutical_form_raw: string;
};

type SearchMode = "brand" | "substance";

export default function Home() {
  const [mode, setMode] = useState<SearchMode>("brand");
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<SearchItem[]>([]);
  const [suggestions, setSuggestions] = useState<SearchItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [suggestionsLoading, setSuggestionsLoading] = useState(false);
  const [error, setError] = useState("");
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [activeIndex, setActiveIndex] = useState(-1);

  const wrapperRef = useRef<HTMLDivElement | null>(null);
  const debounceRef = useRef<NodeJS.Timeout | null>(null);

  const endpoint =
    mode === "brand" ? "/search/brand" : "/search/substance";

  const placeholder =
    mode === "brand"
      ? "Wpisz nazwę leku, np. Zoloft 50 mg"
      : "Wpisz substancję czynną, np. sertralina";

  const examples =
    mode === "brand"
      ? ["Apap", "Zoloft 50 mg", "Gripex"]
      : ["sertralina", "paracetamol", "amoksycylina"];

  const fetchSuggestions = async (value: string) => {
    if (value.trim().length < 2) {
      setSuggestions([]);
      setShowSuggestions(false);
      setActiveIndex(-1);
      return;
    }

    try {
      setSuggestionsLoading(true);

      const res = await fetch(
        `${API_URL}${endpoint}?q=${encodeURIComponent(value)}`
      );

      if (!res.ok) {
        throw new Error(`HTTP ${res.status}`);
      }

      const data = await res.json();
      setSuggestions(data.items ?? []);
      setShowSuggestions(true);
      setActiveIndex(-1);
    } catch (err) {
      console.error(err);
      setSuggestions([]);
      setShowSuggestions(false);
      setActiveIndex(-1);
    } finally {
      setSuggestionsLoading(false);
    }
  };

  useEffect(() => {
    if (debounceRef.current) {
      clearTimeout(debounceRef.current);
    }

    if (query.trim().length < 2) {
      setSuggestions([]);
      setShowSuggestions(false);
      setActiveIndex(-1);
      return;
    }

    debounceRef.current = setTimeout(() => {
      fetchSuggestions(query);
    }, 250);

    return () => {
      if (debounceRef.current) {
        clearTimeout(debounceRef.current);
      }
    };
  }, [query, mode]);

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (
        wrapperRef.current &&
        !wrapperRef.current.contains(event.target as Node)
      ) {
        setShowSuggestions(false);
        setActiveIndex(-1);
      }
    };

    document.addEventListener("mousedown", handleClickOutside);

    return () => {
      document.removeEventListener("mousedown", handleClickOutside);
    };
  }, []);

  const search = async () => {
    if (query.trim().length < 2) {
      setError("Wpisz co najmniej 2 znaki.");
      setResults([]);
      return;
    }

    try {
      setLoading(true);
      setError("");
      setShowSuggestions(false);
      setActiveIndex(-1);

      const res = await fetch(
        `${API_URL}${endpoint}?q=${encodeURIComponent(query)}`
      );

      if (!res.ok) {
        throw new Error(`HTTP ${res.status}`);
      }

      const data = await res.json();
      setResults(data.items ?? []);
    } catch (err) {
      console.error(err);
      setError("Nie udało się pobrać wyników z API.");
      setResults([]);
    } finally {
      setLoading(false);
    }
  };

  const handleSuggestionClick = (item: SearchItem) => {
    window.location.href = `/product/${item.id}`;
  };

  const switchMode = (newMode: SearchMode) => {
    setMode(newMode);
    setQuery("");
    setResults([]);
    setSuggestions([]);
    setError("");
    setShowSuggestions(false);
    setActiveIndex(-1);
  };

  return (
    <main className="min-h-screen bg-slate-50">
      <div className="mx-auto max-w-6xl px-4 py-8 sm:px-6 sm:py-10 lg:px-8">
        <section className="mb-8 rounded-3xl border border-slate-200 bg-white p-6 shadow-sm sm:p-8">
<div className="max-w-4xl">
  <div className="mb-4 flex items-center gap-4">
    <div className="flex h-14 w-14 items-center justify-center overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm">
      <Image
        src="/logo.png"
        alt="Logo aplikacji"
        width={44}
        height={44}
        className="h-auto w-auto object-contain"
        priority
      />
    </div>

    <div className="inline-flex items-center rounded-full border border-sky-200 bg-sky-50 px-3 py-1 text-sm font-medium text-sky-700">
      Narzędzie wspomagające pracę personelu medycznego
    </div>
  </div>

  <h1 className="text-3xl font-bold tracking-tight text-slate-900 sm:text-5xl">
    Wyszukiwanie leków i zamienników
  </h1>

            <p className="mt-4 text-sm leading-6 text-slate-600 sm:text-base">
              Wyszukuj produkt po nazwie handlowej lub substancji czynnej, a następnie
              przejdź do analizy możliwych zamienników na podstawie składu, mocy i postaci.
            </p>
          </div>

          <div className="mt-6 flex flex-wrap gap-3">
            <button
              type="button"
              onClick={() => switchMode("brand")}
              className={`rounded-2xl px-4 py-2 text-sm font-medium transition ${
                mode === "brand"
                  ? "bg-sky-700 text-white"
                  : "border border-slate-200 bg-white text-slate-700 hover:bg-slate-50"
              }`}
            >
              Nazwa handlowa
            </button>

            <button
              type="button"
              onClick={() => switchMode("substance")}
              className={`rounded-2xl px-4 py-2 text-sm font-medium transition ${
                mode === "substance"
                  ? "bg-sky-700 text-white"
                  : "border border-slate-200 bg-white text-slate-700 hover:bg-slate-50"
              }`}
            >
              Substancja czynna
            </button>
          </div>

          <div className="mt-6 rounded-2xl border border-slate-200 bg-slate-50 p-3 sm:p-4">
            <div className="relative" ref={wrapperRef}>
              <div className="flex flex-col gap-3 sm:flex-row">
                <input
                  className="w-full rounded-2xl border border-slate-300 bg-white px-4 py-3 text-base text-slate-900 outline-none transition focus:border-sky-400 focus:ring-4 focus:ring-sky-100"
                  placeholder={placeholder}
                  value={query}
                  onChange={(e) => {
                    setQuery(e.target.value);
                    setError("");
                    setActiveIndex(-1);
                  }}
                  onFocus={() => {
                    if (suggestions.length > 0) {
                      setShowSuggestions(true);
                    }
                  }}
                  onKeyDown={(e) => {
                    if (e.key === "ArrowDown") {
                      e.preventDefault();
                      setShowSuggestions(true);
                      setActiveIndex((prev) =>
                        prev < suggestions.length - 1 ? prev + 1 : prev
                      );
                    }

                    if (e.key === "ArrowUp") {
                      e.preventDefault();
                      setActiveIndex((prev) => (prev > 0 ? prev - 1 : 0));
                    }

                    if (e.key === "Enter") {
                      e.preventDefault();

                      if (activeIndex >= 0 && suggestions[activeIndex]) {
                        handleSuggestionClick(suggestions[activeIndex]);
                      } else {
                        search();
                      }
                    }

                    if (e.key === "Escape") {
                      setShowSuggestions(false);
                      setActiveIndex(-1);
                    }
                  }}
                />

                <button
                  onClick={search}
                  className="rounded-2xl bg-sky-700 px-5 py-3 font-medium text-white transition hover:bg-sky-800"
                >
                  Wyszukaj
                </button>
              </div>

              {showSuggestions && query.trim().length >= 2 && (
                <div className="absolute z-20 mt-2 w-full overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-lg">
                  {suggestionsLoading && (
                    <div className="px-4 py-3 text-sm text-slate-500">
                      Wyszukiwanie podpowiedzi...
                    </div>
                  )}

                  {!suggestionsLoading && suggestions.length === 0 && (
                    <div className="px-4 py-3 text-sm text-slate-500">
                      Brak podpowiedzi.
                    </div>
                  )}

                  {!suggestionsLoading &&
                    suggestions.map((item, index) => (
                      <button
                        key={item.id}
                        type="button"
                        onClick={() => handleSuggestionClick(item)}
                        className={`block w-full border-b border-slate-100 px-4 py-3 text-left transition last:border-b-0 ${
                          index === activeIndex
                            ? "bg-sky-50"
                            : "hover:bg-slate-50"
                        }`}
                      >
                        <div className="font-medium text-slate-900">
                          {item.brand_name}
                        </div>
                        <div className="mt-1 text-sm text-slate-600">
                          {item.common_name}
                        </div>
                        <div className="mt-1 text-xs text-slate-500">
                          {item.strength_raw} • {item.pharmaceutical_form_raw}
                        </div>
                      </button>
                    ))}
                </div>
              )}
            </div>

            <div className="mt-3 flex flex-wrap gap-2 text-xs text-slate-500 sm:text-sm">
              {examples.map((example) => (
                <span
                  key={example}
                  className="rounded-full border border-slate-200 bg-white px-3 py-1"
                >
                  Przykład: {example}
                </span>
              ))}
            </div>
          </div>

          <div className="mt-5 rounded-2xl border border-amber-200 bg-amber-50 p-4">
            <div className="text-sm font-semibold text-amber-800">
              Zastrzeżenie kliniczne
            </div>
            <p className="mt-2 text-sm leading-6 text-amber-900">
              Narzędzie ma charakter wspomagający. Wyniki opierają się na dopasowaniu
              danych o produkcie leczniczym. Ostateczną decyzję terapeutyczną oraz decyzję
              o zamianie produktu leczniczego podejmuje lekarz lub farmaceuta.
            </p>
          </div>

          {loading && (
            <div className="mt-4 rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm text-slate-600">
              Ładowanie wyników...
            </div>
          )}

          {error && (
            <div className="mt-4 rounded-2xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
              {error}
            </div>
          )}
        </section>

        <section className="space-y-4">
          {!loading && !error && results.length > 0 && (
            <>
              <div className="flex items-center justify-between">
                <h2 className="text-lg font-semibold text-slate-900 sm:text-xl">
                  Wyniki wyszukiwania
                </h2>
                <div className="text-sm text-slate-500">{results.length} wyników</div>
              </div>

              <div className="grid gap-4">
                {results.map((item) => (
                  <div
                    key={item.id}
                    className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm transition hover:shadow-md"
                  >
                    <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
                      <div className="min-w-0 flex-1">
                        <div className="flex flex-wrap items-center gap-2">
                          <h3 className="text-xl font-semibold text-slate-900">
                            {item.brand_name}
                          </h3>
                          <span className="rounded-full bg-sky-50 px-2.5 py-1 text-xs font-medium text-sky-700">
                            {mode === "brand" ? "Produkt handlowy" : "Dopasowanie po substancji"}
                          </span>
                        </div>

                        <p className="mt-2 text-sm text-slate-700">{item.common_name}</p>

                        <div className="mt-4 grid gap-3 sm:grid-cols-2">
                          <div className="rounded-2xl bg-slate-50 p-3">
                            <div className="text-xs font-medium uppercase tracking-wide text-slate-500">
                              Substancja czynna
                            </div>
                            <div className="mt-1 text-sm text-slate-800">
                              {item.active_substance_raw}
                            </div>
                          </div>

                          <div className="rounded-2xl bg-slate-50 p-3">
                            <div className="text-xs font-medium uppercase tracking-wide text-slate-500">
                              Moc i postać
                            </div>
                            <div className="mt-1 text-sm text-slate-800">
                              {item.strength_raw}
                              <span className="text-slate-500"> • </span>
                              {item.pharmaceutical_form_raw}
                            </div>
                          </div>
                        </div>
                      </div>

                      <div className="lg:w-[240px]">
                        <a
                          href={`/product/${item.id}`}
                          className="inline-flex w-full items-center justify-center rounded-2xl bg-sky-700 px-4 py-3 text-sm font-medium text-white transition hover:bg-sky-800"
                        >
                          Otwórz analizę zamienników
                        </a>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </>
          )}

          {!loading && !error && results.length === 0 && query.trim().length >= 2 && (
            <div className="rounded-3xl border border-slate-200 bg-white p-8 text-center shadow-sm">
              <div className="text-lg font-semibold text-slate-900">Brak wyników</div>
              <p className="mt-2 text-sm text-slate-600">
                Spróbuj wpisać bardziej precyzyjną nazwę handlową albo substancję czynną.
              </p>
            </div>
          )}
        </section>
      </div>
    </main>
  );
}