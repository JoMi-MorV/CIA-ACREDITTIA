"use client";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Sidebar from "@/components/Sidebar";
import { currentUser } from "@/lib/api";

export default function AppLayout({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const [listo, setListo] = useState(false);

  useEffect(() => {
    if (!currentUser()) router.replace("/login");
    else setListo(true);
  }, [router]);

  if (!listo) return null;
  return (
    <div className="min-h-screen md:flex">
      <Sidebar />
      <main className="min-w-0 flex-1 overflow-x-auto px-4 pb-8 pt-20 md:px-7 md:pt-7">{children}</main>
    </div>
  );
}
