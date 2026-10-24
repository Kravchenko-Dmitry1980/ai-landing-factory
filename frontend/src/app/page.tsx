import { NewLanding } from "@/components/home/NewLanding";
import { ProjectList } from "@/components/home/ProjectList";
import { AppHeader } from "@/components/shell/AppHeader";

const HOW_IT_WORKS = [
  "Загрузите материалы проекта: презентацию, документ или отчёт.",
  "Поправьте текст прямо на странице. Что нужно дополнить, выделено розовым маркером.",
  "Скачайте сайт одним файлом и передайте его администратору сайта университета.",
];

export default function HomePage() {
  return (
    <>
      <AppHeader>
        <a href="#how" className="text-[15px] text-scheme no-underline hover:text-scheme-hover">
          Как это работает
        </a>
      </AppHeader>
      <main className="mx-auto flex max-w-[1200px] flex-col gap-14 px-6 pb-20 pt-10">
        <NewLanding />
        <ProjectList />
        <section id="how" aria-labelledby="how-title" className="flex max-w-[760px] flex-col gap-4 scroll-mt-6">
          <h2 id="how-title" className="font-display text-[30px] font-semibold">
            Как это работает
          </h2>
          <ol className="flex flex-col gap-3 pl-6 text-[17px] leading-relaxed marker:font-semibold marker:text-scheme">
            {HOW_IT_WORKS.map((step) => (
              <li key={step} className="list-decimal pl-1">
                {step}
              </li>
            ))}
          </ol>
        </section>
      </main>
    </>
  );
}
