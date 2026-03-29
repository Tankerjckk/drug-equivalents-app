"use client";

import Image from "next/image";
import { useEffect, useMemo, useState } from "react";
import { useParams } from "next/navigation";
import { API_URL } from "../../../lib/api";

type EquivalentItem = {
  id: number;
  brand_name: string;
  common_name?: string;
  strength_raw?: string;
  label?: string;
  score?: number;
  reason_tags?: string[];
  criteria?: {
    same_active_substances?: boolean;
    same_strength_set?: boolean;
    same_form?: boolean;
  };
};

type PharmacyResponse = {
  base: {
    id: number;
    brand_name: string;
    common_name?: string;
    active_substance_raw?: string;
    strength_raw?: string;
    pharmaceutical_form_raw?: string;
    authorization_number?: string;
    atc_code?: string;
    ma_holder?: string;
    package_description?: string;
    leaflet_url?: string;
    characteristic_url?: string;
  };
  ideal: EquivalentItem[];
  acceptable: EquivalentItem[];
  all_items: EquivalentItem[];
  meta: {
    ideal_count: number;
    acceptable_count: number;
    all_count: number;
  };
};

function CriteriaBadge({
  label,
  active,
}: {
  label: string;
  active: boolean;
}) {
  return (
    <span
      className={`rounded-full px-2.5 py-1 text-xs font-medium ${
        active
          ? "bg-emerald-100 text-emerald-700"
          : "bg-slate-100 text-slate-500"
      }`}
    >
      {label}
    </span>
  );
}

function DetailCard({
  label,
  value,
}: {
  label: string;
  value?: string | null;
}) {
  return (
    <div className="rounded-2xl bg-slate-50 p-4">
      <div className="text-xs font-medium uppercase tracking-wide text-slate-500">
        {label}
      </div>
      <div className="mt-1 text-sm text-slate-800">
        {value && value.trim().length > 0 ? value : "Brak danych"}
      </div>
    </div>
  );
}

function ResultCard({
  item,
  tone,
}: {
  item: EquivalentItem;
  tone: "ideal" | "acceptable";
}) {
  const toneClasses =
    tone === "ideal"
      ? "border-emerald-200 bg-emerald-50"
      : "border-sky-200 bg-sky-50";

  const badgeClasses =
    tone === "ideal"
      ? "bg-emerald-100 text-emerald-700"
      : "bg-sky-100 text-sky-700";

  return (
    <div className={`rounded-3xl border p-5 shadow-sm ${toneClasses}`}>
      <div className="flex flex-wrap items-center gap-2">
        <h3 className="text-lg font-semibold text-slate-900">{item.brand_name}</h3>
        <span className={`rounded-full px-2.5 py-1 text-xs font-medium ${badgeClasses}`}>
          {tone === "ideal" ? "Idealny" : "Akceptowalny"}
        </span>
      </div>

      <p className="mt-2 text-sm text-slate-700">{item.common_name}</p>

      <div className="mt-3 rounded-2xl bg-white/80 p-3">
        <div className="text-xs font-medium uppercase tracking-wide text-slate-500">
          Moc
        </div>
        <div className="mt-1 text-sm text-slate-800">{item.strength_raw}</div>
      </div>

      <div className="mt-4">
        <div className="text-xs font-medium uppercase tracking-wide text-slate-500">
          Kryteria zgodności
        </div>
        <div className="mt-2 flex flex-wrap gap-2">
          <CriteriaBadge
            label="Ta sama substancja"
            active={Boolean(item.criteria?.same_active_substances)}
          />
          <CriteriaBadge
            label="Ta sama moc"
            active={Boolean(item.criteria?.same_strength_set)}
          />
          <CriteriaBadge
            label="Ta sama postać"
            active={Boolean(item.criteria?.same_form)}
          />
        </div>
      </div>

      {item.reason_tags && item.reason_tags.length > 0 && (
        <div className="mt-4">
          <div className="text-xs font-medium uppercase tracking-wide text-slate-500">
            Uzasadnienie dopasowania
          </div>
          <div className="mt-2 flex flex-wrap gap-2">
            {item.reason_tags.map((tag) => (
              <span
                key={tag}
                className="rounded-full border border-slate-200 bg-white px-2.5 py-1 text-xs text-slate-700"
              >
                {tag}
              </span>
            ))}
          </div>
        </div>
      )}

      <div className="mt-4 text-sm font-medium text-slate-700">{item.label}</div>
    </div>
  );
}

export default function ProductPage() {
  const params = useParams();
  const id = params.id as string;

  const [data, setData] = useState<PharmacyResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const [showOnlyIdeal, setShowOnlyIdeal] = useState(false);
  const [requireSameSubstance, setRequireSameSubstance] = useState(true);
  const [requireSameStrength, setRequireSameStrength] = useState(false);
  const [requireSameForm, setRequireSameForm] = useState(false);

  useEffect(() => {
    const load = async () => {
      try {
        setLoading(true);
        setError("");

        const res = await fetch(`${API_URL}/products/${id}/pharmacy-equivalents`);

        if (!res.ok) {
          throw new Error(`HTTP ${res.status}`);
        }

        const json = await res.json();
        setData(json);
      } catch (err) {
        console.error(err);
        setError("Nie udało się pobrać danych produktu.");
      } finally {
        setLoading(false);
      }
    };

    if (id) {
      load();
    }
  }, [id]);

  const filteredItems = useMemo(() => {
    if (!data) return [];

    let items = [...data.all_items];

    if (showOnlyIdeal) {
      items = items.filter((item) => item.score === 100);
    }

    if (requireSameSubstance) {
      items = items.filter((item) => item.criteria?.same_active_substances);
    }

    if (requireSameStrength) {
      items = items.filter((item) => item.criteria?.same_strength_set);
    }

    if (requireSameForm) {
      items = items.filter((item) => item.criteria?.same_form);
    }

    return items;
  }, [data, showOnlyIdeal, requireSameSubstance, requireSameStrength, requireSameForm]);

  const filteredIdeal = filteredItems.filter((item) => item.score === 100);
  const filteredAcceptable = filteredItems.filter((item) => item.score === 80);

  if (loading) {
    return (
      <main className="min-h-screen bg-slate-50">
        <div className="mx-auto max-w-6xl px-4 py-10 sm:px-6 lg:px-8">
          <div className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm">
            Ładowanie...
          </div>
        </div>
      </main>
    );
  }

  if (error) {
    return (
      <main className="min-h-screen bg-slate-50">
        <div className="mx-auto max-w-6xl px-4 py-10 sm:px-6 lg:px-8">
          <div className="rounded-3xl border border-red-200 bg-red-50 p-6 text-red-700 shadow-sm">
            {error}
          </div>
        </div>
      </main>
    );
  }

  if (!data) {
    return (
      <main className="min-h-screen bg-slate-50">
        <div className="mx-auto max-w-6xl px-4 py-10 sm:px-6 lg:px-8">
          <div className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm">
            Brak danych.
          </div>
        </div>
      </main>
    );
  }

  return (
    <main className="min-h-screen bg-slate-50">
      <div className="mx-auto max-w-6xl px-4 py-8 sm:px-6 sm:py-10 lg:px-8">
        <a
          href="/"
          className="inline-flex items-center rounded-full border border-slate-200 bg-white px-4 py-2 text-sm text-slate-600 shadow-sm transition hover:bg-slate-100"
        >
          ← Powrót do wyszukiwania
        </a>

        <section className="mt-6 rounded-3xl border border-slate-200 bg-white p-6 shadow-sm sm:p-8">
          <div className="mb-6 flex items-center gap-3">
            <div className="flex h-12 w-12 items-center justify-center overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm">
              <Image
                src="/logo.png"
                alt="Logo aplikacji"
                width={36}
                height={36}
                className="h-auto w-auto object-contain"
                priority
              />
            </div>

            <div className="text-sm font-medium text-slate-500">
              Moduł analizy zamienników
            </div>
          </div>

          <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
            <div className="max-w-3xl">
              <div className="mb-3 inline-flex items-center rounded-full bg-sky-50 px-3 py-1 text-sm font-medium text-sky-700">
                Produkt referencyjny
              </div>

              <h1 className="text-3xl font-bold tracking-tight text-slate-900 sm:text-4xl">
                {data.base.brand_name}
              </h1>

              <p className="mt-3 text-sm text-slate-700 sm:text-base">
                {data.base.common_name}
              </p>
            </div>

            <div className="grid grid-cols-2 gap-3 lg:w-[260px]">
              <div className="rounded-2xl bg-emerald-50 p-4 text-center">
                <div className="text-2xl font-bold text-emerald-700">
                  {filteredIdeal.length}
                </div>
                <div className="mt-1 text-xs uppercase tracking-wide text-emerald-700">
                  Idealne
                </div>
              </div>

              <div className="rounded-2xl bg-sky-50 p-4 text-center">
                <div className="text-2xl font-bold text-sky-700">
                  {filteredAcceptable.length}
                </div>
                <div className="mt-1 text-xs uppercase tracking-wide text-sky-700">
                  Akceptowalne
                </div>
              </div>
            </div>
          </div>

          <div className="mt-5 grid gap-3 md:grid-cols-2 xl:grid-cols-3">
            <DetailCard label="Substancja czynna" value={data.base.active_substance_raw} />
            <DetailCard label="Moc i postać" value={`${data.base.strength_raw ?? "Brak danych"} • ${data.base.pharmaceutical_form_raw ?? "Brak danych"}`} />
            <DetailCard label="Numer pozwolenia" value={data.base.authorization_number} />
            <DetailCard label="Kod ATC" value={data.base.atc_code} />
            <DetailCard label="Podmiot odpowiedzialny" value={data.base.ma_holder} />
            <DetailCard label="Opakowanie" value={data.base.package_description} />
          </div>

          <div className="mt-5 flex flex-wrap gap-3">
            {data.base.leaflet_url && (
              <a
                href={data.base.leaflet_url}
                target="_blank"
                rel="noreferrer"
                className="inline-flex items-center rounded-2xl border border-slate-200 bg-white px-4 py-2 text-sm font-medium text-slate-700 shadow-sm hover:bg-slate-50"
              >
                Otwórz ulotkę
              </a>
            )}

            {data.base.characteristic_url && (
              <a
                href={data.base.characteristic_url}
                target="_blank"
                rel="noreferrer"
                className="inline-flex items-center rounded-2xl border border-slate-200 bg-white px-4 py-2 text-sm font-medium text-slate-700 shadow-sm hover:bg-slate-50"
              >
                Otwórz ChPL
              </a>
            )}
          </div>

          <div className="mt-6 rounded-2xl border border-amber-200 bg-amber-50 p-4">
            <div className="text-sm font-semibold text-amber-800">
              Zastrzeżenie kliniczne
            </div>
            <p className="mt-2 text-sm leading-6 text-amber-900">
              Wyniki mają charakter wspomagający i opierają się na dopasowaniu cech
              produktu leczniczego, w tym składu, mocy i postaci farmaceutycznej.
              Ostateczną decyzję o zastosowaniu lub zamianie produktu leczniczego
              podejmuje lekarz albo farmaceuta.
            </p>
          </div>
        </section>

        <section className="mt-8 rounded-3xl border border-slate-200 bg-white p-6 shadow-sm">
          <div className="mb-4">
            <h2 className="text-2xl font-semibold text-slate-900">
              Filtry analizy
            </h2>
            <p className="mt-2 text-sm text-slate-600">
              Zawęź wyniki do kryteriów istotnych klinicznie.
            </p>
          </div>

          <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-4">
            <label className="flex items-center gap-3 rounded-2xl border border-slate-200 bg-slate-50 p-4">
              <input
                type="checkbox"
                checked={showOnlyIdeal}
                onChange={(e) => setShowOnlyIdeal(e.target.checked)}
                className="h-4 w-4"
              />
              <span className="text-sm text-slate-800">Tylko idealne</span>
            </label>

            <label className="flex items-center gap-3 rounded-2xl border border-slate-200 bg-slate-50 p-4">
              <input
                type="checkbox"
                checked={requireSameSubstance}
                onChange={(e) => setRequireSameSubstance(e.target.checked)}
                className="h-4 w-4"
              />
              <span className="text-sm text-slate-800">Ta sama substancja</span>
            </label>

            <label className="flex items-center gap-3 rounded-2xl border border-slate-200 bg-slate-50 p-4">
              <input
                type="checkbox"
                checked={requireSameStrength}
                onChange={(e) => setRequireSameStrength(e.target.checked)}
                className="h-4 w-4"
              />
              <span className="text-sm text-slate-800">Ta sama moc</span>
            </label>

            <label className="flex items-center gap-3 rounded-2xl border border-slate-200 bg-slate-50 p-4">
              <input
                type="checkbox"
                checked={requireSameForm}
                onChange={(e) => setRequireSameForm(e.target.checked)}
                className="h-4 w-4"
              />
              <span className="text-sm text-slate-800">Ta sama postać</span>
            </label>
          </div>
        </section>

        <section className="mt-8">
          <div className="mb-4 flex items-center justify-between">
            <h2 className="text-2xl font-semibold text-slate-900">
              Idealne zamienniki
            </h2>
          </div>

          {filteredIdeal.length === 0 ? (
            <div className="rounded-3xl border border-slate-200 bg-white p-6 text-slate-500 shadow-sm">
              Brak wyników spełniających aktualne filtry.
            </div>
          ) : (
            <div className="grid gap-4 md:grid-cols-2">
              {filteredIdeal.map((item) => (
                <ResultCard key={item.id} item={item} tone="ideal" />
              ))}
            </div>
          )}
        </section>

        <section className="mt-8">
          <div className="mb-4 flex items-center justify-between">
            <h2 className="text-2xl font-semibold text-slate-900">
              Akceptowalne zamienniki
            </h2>
          </div>

          {filteredAcceptable.length === 0 ? (
            <div className="rounded-3xl border border-slate-200 bg-white p-6 text-slate-500 shadow-sm">
              Brak wyników spełniających aktualne filtry.
            </div>
          ) : (
            <div className="grid gap-4 md:grid-cols-2">
              {filteredAcceptable.map((item) => (
                <ResultCard key={item.id} item={item} tone="acceptable" />
              ))}
            </div>
          )}
        </section>
      </div>
    </main>
  );
}