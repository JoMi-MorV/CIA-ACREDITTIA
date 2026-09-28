"use client";
import { useRouter } from "next/navigation";
import { useEffect } from "react";

/** La ruta histórica /ops redirige a la consola administrativa unificada. */
export default function OpsIndex() {
  const router = useRouter();
  useEffect(() => { router.replace("/admin/dashboard"); }, [router]);
  return null;
}
