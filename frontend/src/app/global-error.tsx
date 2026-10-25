"use client";

/** Последний рубеж: упал сам каркас страницы, поэтому здесь нет общих стилей и шрифтов. */
export default function GlobalError({ reset }: { error: Error & { digest?: string }; reset: () => void }) {
  return (
    <html lang="ru">
      <body style={{ margin: 0, minHeight: "100vh", display: "flex", alignItems: "center", justifyContent: "center", background: "#F6F7FB", color: "#22262E", font: "18px/1.6 system-ui, sans-serif" }}>
        <main style={{ maxWidth: 520, padding: 24 }}>
          <h1 style={{ fontSize: 28, margin: "0 0 12px" }}>Ленд не открылся</h1>
          <p style={{ margin: "0 0 20px" }}>Сервер сейчас не отвечает. Подождите минуту и попробуйте ещё раз.</p>
          <button type="button" onClick={() => reset()} style={{ height: 44, padding: "0 20px", border: 0, borderRadius: 10, background: "#1E5FD8", color: "#fff", fontSize: 15, fontWeight: 600, cursor: "pointer" }}>
            Повторить
          </button>
        </main>
      </body>
    </html>
  );
}
