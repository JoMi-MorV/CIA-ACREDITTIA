"use client";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import * as Api from "@/lib/cliente";

const ITEMS = [
  { href: "/dashboard", icono: "⌂", nombre: "Inicio" },
  { href: "/contratos", icono: "▤", nombre: "Contratos" },
  { href: "/faenas", icono: "◇", nombre: "Faenas" },
  { href: "/personal", icono: "◎", nombre: "Personal" },
  { href: "/equipos", icono: "▣", nombre: "Equipos" },
  { href: "/reportes", icono: "▥", nombre: "Reportes" },
  { href: "/alertas", icono: "!", nombre: "Alertas" },
  { href: "/calendario", icono: "□", nombre: "Calendario" },
  { href: "/perfil", icono: "○", nombre: "Mi perfil" },
];

export default function Sidebar() {
  const path = usePathname();
  const router = useRouter();
  const [noLeidas, setNoLeidas] = useState(0);
  const user = typeof window !== "undefined" ? Api.currentUser() : null;
  const esAdmin = user?.role === "admin";
  const empresaImpersonada = typeof window !== "undefined" ? sessionStorage.getItem("impersonar") : null;
  const impersonando = typeof window !== "undefined" ? sessionStorage.getItem("impersonar_nombre") : null;
  const viendoEmpresa = Boolean(empresaImpersonada || impersonando);

  useEffect(() => {
    if (esAdmin && !impersonando) return;
    Api.alertas.resumen().then((r) => setNoLeidas(r.no_leidas)).catch(() => {});
  }, [path, esAdmin, impersonando]);

  const salir = async () => {
    // Se revoca el refresh token en el servidor antes de limpiar la sesión: si
    // solo se borrara del navegador el token seguiría siendo válido hasta caducar.
    const refresh = Api.refreshToken();
    if (refresh) await Api.auth.logout(refresh).catch(() => {});
    Api.clearSession();
    sessionStorage.clear();
    router.push("/login");
  };

  // Para un contract_admin el rótulo útil es su contrato, no la empresa.
  const subtitulo = esAdmin ? "Administración"
    : user?.contrato?.nombre ?? user?.company?.nombre ?? "";

  return (
    <aside className="fixed inset-x-0 top-0 z-40 flex h-16 items-center border-b border-white/10 bg-brand text-white md:sticky md:h-screen md:w-60 md:shrink-0 md:flex-col md:items-stretch md:border-b-0 md:border-r md:px-3 md:py-5">
      <div className="flex items-center gap-3 px-4 md:block md:px-2 md:pb-5">
        <div className="text-[17px] font-extrabold tracking-[0.16em]">ACREDITTIA</div>
        <div className="hidden text-[11px] text-white/55 md:block">{subtitulo}</div>
      </div>
      {esAdmin && viendoEmpresa && (
        <div className="absolute left-2 top-16 z-50 flex items-center gap-2 rounded-md bg-amber-600 px-3 py-2 text-xs font-semibold text-white shadow md:static md:mx-3 md:mb-2 md:shadow-none">
          Viendo como {impersonando ?? "empresa"}
          <button className="ml-2 underline" onClick={() => {
            sessionStorage.removeItem("impersonar");
            sessionStorage.removeItem("impersonar_nombre");
            router.push("/admin/dashboard");
          }}>Volver a consola interna</button>
        </div>
      )}
      <nav className="ml-auto flex max-w-[calc(100vw-145px)] gap-1 overflow-x-auto px-2 md:ml-0 md:max-w-none md:flex-1 md:flex-col md:gap-1 md:overflow-visible md:px-0">
        {esAdmin && !viendoEmpresa && (
          <Link href="/admin/dashboard" className={`flex items-center gap-3 rounded-md px-3 py-2 text-sm ${path.startsWith("/admin") ? "bg-accent font-semibold" : "hover:bg-white/10"}`}>
            <span className="grid h-5 w-5 place-items-center border border-current/60 text-xs">+</span><span className="hidden md:inline">Panel admin</span>
          </Link>
        )}
        {(!esAdmin || viendoEmpresa) && ITEMS
          .filter((i) => !(viendoEmpresa && i.href === "/perfil"))
          .filter((i) => !(user?.role === "contract_admin" && i.href === "/reportes"))
          .map((i) => (
          <Link key={i.href} href={i.href}
            className={`flex shrink-0 items-center gap-3 rounded-md px-3 py-2 text-sm ${path.startsWith(i.href) ? "bg-accent font-semibold" : "hover:bg-white/10"}`}>
            <span className="grid h-5 w-5 place-items-center border border-current/60 text-xs">{i.icono}</span><span className="hidden md:inline">{i.nombre}</span>
            {i.href === "/alertas" && noLeidas > 0 && (
              <span className="ml-auto hidden rounded-full bg-red-500 px-2 py-0.5 text-xs font-bold md:inline">{noLeidas}</span>
            )}
          </Link>
        ))}
      </nav>
      <button onClick={salir} className="hidden rounded-md px-3 py-2 text-left text-sm text-white/60 hover:bg-white/10 md:block">
        ↪ Cerrar sesión
      </button>
    </aside>
  );
}
