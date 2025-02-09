try:
    import gc
    import torch

    def torch_gc():
        """Performs garbage collection for both Python and PyTorch CUDA tensors.

        This function collects Python garbage and clears the PyTorch CUDA cache
        and IPC (Inter-Process Communication) resources.
        """

        from comfy import model_management as mg

        for model in mg.current_loaded_models:
            if hasattr(model, "model"):
                if hasattr(model.model, "to"):
                    model.model.to("cpu")
                if hasattr(model.model, "model"):
                    model.model.model.to("cpu")
        mg.current_loaded_models.clear()

        gc.collect()  # Collect Python garbage
        torch.cuda.empty_cache()  # Clear PyTorch CUDA cache
        torch.cuda.ipc_collect()  # Clear PyTorch CUDA IPC resources

except:

    def torch_gc():
        """Dummy function when torch is not available.

        This function does nothing and serves as a placeholder when torch is
        not available, allowing the rest of the code to run without errors.
        """
        pass
