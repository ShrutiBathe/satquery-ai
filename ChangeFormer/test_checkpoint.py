from types import SimpleNamespace
from models.basic_model import CDEvaluator

args = SimpleNamespace(
    n_class=2,
    gpu_ids=[],
    net_G="ChangeFormerV6",
    embed_dim=256,
    checkpoint_dir="/mnt/d/Projects/satquery-ai/ChangeFormer/checkpoints/ChangeFormer_LEVIR/CD_ChangeFormerV6_LEVIR_b16_lr0.0001_adamw_train_test_200_linear_ce_multi_train_True_multi_infer_False_shuffle_AB_False_embed_dim_256",
    checkpoint_name="best_ckpt.pt",
    output_folder="outputs/test_checkpoint",
)

print("Creating ChangeFormerV6...")
model = CDEvaluator(args)

print("Loading checkpoint...")
model.load_checkpoint("best_ckpt.pt")

print("Checkpoint loaded successfully!")
print("Device:", model.device)
print("Model:", args.net_G)
