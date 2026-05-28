import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { UserPlus } from "lucide-react";
import { api } from "../services/api";
import { useAuth } from "../contexts/AuthContext";
import styles from "./Usuarios.module.css";
import pageStyles from "./PageGeneric.module.css";

interface UsuarioItem {
  id: number;
  nome: string;
  email: string;
  perfil: "ADMIN" | "GESTOR" | "COLABORADOR";
  ativo: boolean;
  criado_em: string;
}

interface ModalState {
  tipo: "criar" | "editar";
  usuario?: UsuarioItem;
}

const PERFIS = ["ADMIN", "GESTOR", "COLABORADOR"] as const;

function perfilBadge(perfil: string, ativo: boolean) {
  if (!ativo) return <span className={`${styles.badge} ${styles.inativo}`}>Inativo</span>;
  const cls = perfil === "ADMIN" ? styles.admin : perfil === "GESTOR" ? styles.gestor : styles.colaborador;
  return <span className={`${styles.badge} ${cls}`}>{perfil}</span>;
}

export default function Usuarios() {
  const { usuario: eu } = useAuth();
  const qc = useQueryClient();
  const [modal, setModal] = useState<ModalState | null>(null);
  const [erro, setErro] = useState("");

  const { data: usuarios = [], isLoading } = useQuery<UsuarioItem[]>({
    queryKey: ["usuarios"],
    queryFn: () => api.get<UsuarioItem[]>("/usuarios/").then((r) => r.data),
  });

  const criar = useMutation({
    mutationFn: (payload: { nome: string; email: string; senha: string; perfil: string }) =>
      api.post("/usuarios/", payload).then((r) => r.data),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ["usuarios"] }); setModal(null); setErro(""); },
    onError: (e: { response?: { data?: { detail?: string } } }) =>
      setErro(e.response?.data?.detail ?? "Erro ao criar usuário"),
  });

  const atualizar = useMutation({
    mutationFn: ({ id, payload }: { id: number; payload: { nome?: string; perfil?: string; ativo?: boolean } }) =>
      api.put(`/usuarios/${id}`, payload).then((r) => r.data),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ["usuarios"] }); setModal(null); setErro(""); },
    onError: (e: { response?: { data?: { detail?: string } } }) =>
      setErro(e.response?.data?.detail ?? "Erro ao atualizar usuário"),
  });

  function abrirCriar() { setErro(""); setModal({ tipo: "criar" }); }
  function abrirEditar(u: UsuarioItem) { setErro(""); setModal({ tipo: "editar", usuario: u }); }

  function handleSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const fd = new FormData(e.currentTarget);
    if (modal?.tipo === "criar") {
      criar.mutate({
        nome: fd.get("nome") as string,
        email: fd.get("email") as string,
        senha: fd.get("senha") as string,
        perfil: fd.get("perfil") as string,
      });
    } else if (modal?.tipo === "editar" && modal.usuario) {
      atualizar.mutate({
        id: modal.usuario.id,
        payload: {
          nome: fd.get("nome") as string,
          perfil: fd.get("perfil") as string,
        },
      });
    }
  }

  function toggleAtivo(u: UsuarioItem) {
    atualizar.mutate({ id: u.id, payload: { ativo: !u.ativo } });
  }

  return (
    <div className={pageStyles.page}>
      <div className={pageStyles.card}>
        <div className={pageStyles.cardHeader}>
          <span className={pageStyles.cardTitle}>Usuários do Sistema</span>
          <button className={pageStyles.btnPrimary} onClick={abrirCriar}>
            <UserPlus size={14} style={{ marginRight: 6 }} />
            Novo Usuário
          </button>
        </div>

        {isLoading ? (
          <div className={pageStyles.loadingMsg}>Carregando…</div>
        ) : (
          <div className={pageStyles.tableWrap}>
            <table className={pageStyles.table}>
              <thead>
                <tr>
                  <th>Nome</th>
                  <th>E-mail</th>
                  <th>Perfil</th>
                  <th>Desde</th>
                  <th>Ações</th>
                </tr>
              </thead>
              <tbody>
                {usuarios.map((u) => (
                  <tr key={u.id}>
                    <td>{u.nome}</td>
                    <td>{u.email}</td>
                    <td>{perfilBadge(u.perfil, u.ativo)}</td>
                    <td>{new Date(u.criado_em).toLocaleDateString("pt-BR")}</td>
                    <td>
                      <div className={styles.acoes}>
                        <button className={styles.btnEditar} onClick={() => abrirEditar(u)}>
                          Editar
                        </button>
                        {u.id !== eu?.id && (
                          <button
                            className={u.ativo ? styles.btnDesativar : styles.btnAtivar}
                            onClick={() => toggleAtivo(u)}
                          >
                            {u.ativo ? "Desativar" : "Reativar"}
                          </button>
                        )}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {modal && (
        <div className={styles.overlay} onClick={() => setModal(null)}>
          <div className={styles.modal} onClick={(e) => e.stopPropagation()}>
            <h3 className={styles.modalTitle}>
              {modal.tipo === "criar" ? "Novo Usuário" : "Editar Usuário"}
            </h3>
            <form onSubmit={handleSubmit} style={{ display: "flex", flexDirection: "column", gap: 12 }}>
              <label className={styles.modalField}>
                Nome
                <input name="nome" defaultValue={modal.usuario?.nome} required />
              </label>
              {modal.tipo === "criar" && (
                <>
                  <label className={styles.modalField}>
                    E-mail
                    <input name="email" type="email" required />
                  </label>
                  <label className={styles.modalField}>
                    Senha inicial
                    <input name="senha" type="password" minLength={6} required />
                  </label>
                </>
              )}
              <label className={styles.modalField}>
                Perfil
                <select name="perfil" defaultValue={modal.usuario?.perfil ?? "COLABORADOR"}>
                  {PERFIS.map((p) => (
                    <option key={p} value={p}>{p}</option>
                  ))}
                </select>
              </label>
              {erro && <p className={styles.errorInline}>{erro}</p>}
              <div className={styles.modalActions}>
                <button type="button" className={pageStyles.btnSecondary} onClick={() => setModal(null)}>
                  Cancelar
                </button>
                <button type="submit" className={pageStyles.btnPrimary}>
                  {modal.tipo === "criar" ? "Criar" : "Salvar"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
