import { UploadForm } from "@/components/upload/UploadForm";

export default function HomePage() {
  return (
    <div className="space-y-8">
      <section>
        <h1 className="text-3xl font-bold tracking-tight">AI Landing Factory</h1>
        <p className="mt-2 max-w-2xl text-muted-foreground">
          Content-first: материалы → извлечение → LandingContract → генерация → preview.
        </p>
      </section>
      <UploadForm />
    </div>
  );
}
