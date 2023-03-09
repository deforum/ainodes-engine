import secrets
import threading

import numpy as np
from einops import rearrange

from ainodes_backend.k_sampler import common_ksampler

import torch
from PIL import Image
from PIL.ImageQt import ImageQt
#from qtpy.QtWidgets import QLineEdit, QLabel, QPushButton, QFileDialog, QVBoxLayout
from qtpy import QtWidgets, QtCore, QtGui
from qtpy.QtGui import QPixmap

from ainodes_backend.torch_gc import torch_gc
from ainodes_frontend.nodes.base.node_config import register_node, OP_NODE_K_SAMPLER
from ainodes_frontend.nodes.base.ai_node_base import CalcNode, CalcGraphicsNode
from ainodes_backend.node_engine.node_content_widget import QDMNodeContentWidget
from ainodes_backend.node_engine.utils import dumpException
from ainodes_backend import singleton as gs
from ainodes_backend.worker.worker import Worker

SCHEDULERS = ["karras", "normal", "simple", "ddim_uniform"]
SAMPLERS = ["euler", "euler_ancestral", "heun", "dpm_2", "dpm_2_ancestral",
            "lms", "dpm_fast", "dpm_adaptive", "dpmpp_2s_ancestral", "dpmpp_sde",
            "dpmpp_2m", "ddim", "uni_pc", "uni_pc_bh2"]

class KSamplerWidget(QDMNodeContentWidget):
    def initUI(self):
        # Create a label to display the image
        #self.text_label = QtWidgets.QLabel("K Sampler")

        self.schedulers_layout = QtWidgets.QHBoxLayout()
        self.schedulers_label = QtWidgets.QLabel("Scheduler:")
        self.schedulers = QtWidgets.QComboBox()
        self.schedulers.addItems(SCHEDULERS)
        self.schedulers_layout.addWidget(self.schedulers_label)
        self.schedulers_layout.addWidget(self.schedulers)

        self.sampler_layout = QtWidgets.QHBoxLayout()
        self.sampler_label = QtWidgets.QLabel("Sampler:")
        self.sampler = QtWidgets.QComboBox()
        self.sampler.addItems(SAMPLERS)
        self.sampler_layout.addWidget(self.sampler_label)
        self.sampler_layout.addWidget(self.sampler)

        self.seed_layout = QtWidgets.QHBoxLayout()
        self.seed_label = QtWidgets.QLabel("Seed:")
        self.seed = QtWidgets.QLineEdit()
        self.seed_layout.addWidget(self.seed_label)
        self.seed_layout.addWidget(self.seed)

        self.steps_layout = QtWidgets.QHBoxLayout()
        self.steps_label = QtWidgets.QLabel("Steps:")
        self.steps = QtWidgets.QSpinBox()
        self.steps.setMinimum(1)
        self.steps.setMaximum(1000)
        self.steps.setValue(10)
        self.steps_layout.addWidget(self.steps_label)
        self.steps_layout.addWidget(self.steps)

        self.start_step_layout = QtWidgets.QHBoxLayout()
        self.start_step_label = QtWidgets.QLabel("Start Step:")
        self.start_step = QtWidgets.QSpinBox()
        self.start_step.setMinimum(0)
        self.start_step.setMaximum(1000)
        self.start_step.setValue(0)
        self.start_step_layout.addWidget(self.start_step_label)
        self.start_step_layout.addWidget(self.start_step)

        self.last_step_layout = QtWidgets.QHBoxLayout()
        self.last_step_label = QtWidgets.QLabel("Last Step:")
        self.last_step = QtWidgets.QSpinBox()
        self.last_step.setMinimum(1)
        self.last_step.setMaximum(1000)
        self.last_step.setValue(5)
        self.last_step_layout.addWidget(self.last_step_label)
        self.last_step_layout.addWidget(self.last_step)

        self.stop_early_layout = QtWidgets.QHBoxLayout()
        self.stop_early = QtWidgets.QCheckBox("Stop Sampling Early")
        self.stop_early_label = QtWidgets.QLabel()
        self.stop_early_layout.addWidget(self.stop_early)
        self.stop_early_layout.addWidget(self.stop_early_label)

        palette = QtGui.QPalette()
        palette.setColor(QtGui.QPalette.WindowText, QtGui.QColor("white"))
        palette.setColor(QtGui.QPalette.Disabled, QtGui.QPalette.WindowText, QtGui.QColor("black"))

        self.stop_early.setPalette(palette)

        self.guidance_scale_layout = QtWidgets.QHBoxLayout()
        self.guidance_scale_label = QtWidgets.QLabel("Guidance Scale:")
        self.guidance_scale = QtWidgets.QDoubleSpinBox()
        self.guidance_scale.setMinimum(1.01)
        self.guidance_scale.setMaximum(100.00)
        self.guidance_scale.setSingleStep(0.01)
        self.guidance_scale.setValue(7.50)
        self.guidance_scale_layout.addWidget(self.guidance_scale_label)
        self.guidance_scale_layout.addWidget(self.guidance_scale)

        self.button_layout = QtWidgets.QHBoxLayout()
        self.button = QtWidgets.QPushButton("Run")
        self.fix_seed_button = QtWidgets.QPushButton("Fix Seed")
        self.button_layout.addWidget(self.button)
        self.button_layout.addWidget(self.fix_seed_button)

        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(15,15,15,25)
        layout.addLayout(self.schedulers_layout)
        layout.addLayout(self.sampler_layout)
        layout.addLayout(self.seed_layout)
        layout.addLayout(self.steps_layout)
        layout.addLayout(self.start_step_layout)
        layout.addLayout(self.last_step_layout)
        layout.addLayout(self.stop_early_layout)
        layout.addLayout(self.guidance_scale_layout)
        layout.addLayout(self.button_layout)

        self.setLayout(layout)


    def serialize(self):
        res = super().serialize()
        res['scheduler'] = self.schedulers.currentText()
        res['sampler'] = self.sampler.currentText()
        res['seed'] = self.seed.text()
        res['steps'] = self.steps.value()
        res['guidance_scale'] = self.guidance_scale.value()
        return res

    def deserialize(self, data, hashmap={}):
        res = super().deserialize(data, hashmap)
        try:
            self.schedulers.setCurrentText(data['scheduler'])
            self.sampler.setCurrentText(data['sampler'])
            self.seed.setText(data['seed'])
            self.steps.setValue(data['steps'])
            self.guidance_scale.setValue(data['guidance_scale'])
            return True & res
        except Exception as e:
            dumpException(e)
        return res


@register_node(OP_NODE_K_SAMPLER)
class KSamplerNode(CalcNode):
    icon = "icons/in.png"
    op_code = OP_NODE_K_SAMPLER
    op_title = "K Sampler"
    content_label_objname = "K_sampling_node"
    category = "sampling"
    def __init__(self, scene):
        super().__init__(scene, inputs=[2,3,3,1], outputs=[5,2,1])
        self.content.button.clicked.connect(self.evalImplementation)
        self.busy = False
        # Create a worker object
    def initInnerClasses(self):
        self.content = KSamplerWidget(self)
        self.grNode = CalcGraphicsNode(self)
        self.grNode.height = 420
        self.grNode.width = 256
        self.content.setMinimumWidth(256)
        self.content.setMinimumHeight(256)
        self.input_socket_name = ["EXEC", "COND", "N COND", "LATENT"]
        self.output_socket_name = ["EXEC", "LATENT", "IMAGE"]
        self.seed = ""
        self.content.fix_seed_button.clicked.connect(self.setSeed)
        #self.content.setMinimumHeight(400)
        #self.content.setMinimumWidth(256)
        #self.content.image.changeEvent.connect(self.onInputChanged)

    def evalImplementation(self, index=0):


        self.markDirty(True)
        #self.markInvalid(True)
        #self.busy = False
        if self.value is None:
            # Start the worker thread
            if self.busy == False:
                #self.worker = Worker(self.k_sampling)
                # Connect the worker's finished signal to a slot that updates the node value
                #self.worker.signals.result.connect(self.onWorkerFinished)
                #self.scene.queue.add_task(self.k_sampling)
                #self.scene.queue.task_finished.connect(self.onWorkerFinished)
                self.busy = True
                #self.scene.threadpool.start(self.worker)
                thread0 = threading.Thread(target=self.k_sampling)
                thread0.start()


            return None
        else:
            self.markDirty(False)
            self.markInvalid(False)
            #self.markDescendantsDirty()
            #self.evalChildren()
            return self.value

    def onMarkedDirty(self):
        self.value = None
    def k_sampling(self, progress_callback=None):
        try:
            cond_node, index = self.getInput(2)
            cond = cond_node.getOutput(index)
        except Exception as e:
            print(e)
            cond = None
        try:
            n_cond_node, index = self.getInput(1)
            n_cond = n_cond_node.getOutput(index)
        except:
            n_cond = None
        try:
            latent_node, index = self.getInput(0)
            latent = latent_node.getOutput(index)
        except:
            latent = torch.zeros([1, 4, 512 // 8, 512 // 8])
        self.seed = self.content.seed.text()
        try:
            self.seed = int(self.seed)
        except:
            self.seed = secrets.randbelow(99999999)
        try:
            last_step = self.content.steps.value() if self.content.stop_early.isChecked() == False else self.content.last_step.value()
            sample = common_ksampler(device="cuda",
                                     seed=self.seed,
                                     steps=self.content.steps.value(),
                                     start_step=self.content.start_step.value(),
                                     last_step=last_step,
                                     cfg=self.content.guidance_scale.value(),
                                     sampler_name=self.content.sampler.currentText(),
                                     scheduler=self.content.schedulers.currentText(),
                                     positive=cond,
                                     negative=n_cond,
                                     latent=latent)

            return_sample = sample.cpu().half()

            x_samples = gs.models["sd"].decode_first_stage(sample.half())
            x_samples = torch.clamp((x_samples + 1.0) / 2.0, min=0.0, max=1.0)
            x_sample = 255. * rearrange(x_samples[0].cpu().numpy(), 'c h w -> h w c')
            image = Image.fromarray(x_sample.astype(np.uint8))
            qimage = ImageQt(image)
            pixmap = QPixmap().fromImage(qimage)
            self.value = pixmap
            del sample
            del x_samples
            x_samples = None
            sample = None
            torch_gc()
            self.onWorkerFinished([pixmap, return_sample])
        except:
            self.busy = False
            if len(self.getOutputs(2)) > 0:
                self.executeChild(output_index=2)
        return [pixmap, return_sample]
    @QtCore.Slot(object)
    def onWorkerFinished(self, result):
        # Update the node value and mark it as dirty
        #self.value = result[0]
        print("K SAMPLER:", self.content.steps.value(), "steps,", self.content.sampler.currentText(), " seed: ", self.seed)
        self.markDirty(False)
        self.markInvalid(False)
        self.setOutput(0, result[0])
        self.setOutput(1, result[1])
        self.busy = False
        #self.worker.autoDelete()
        #self.scene.queue.task_finished.disconnect(self.onWorkerFinished)
        if len(self.getOutputs(2)) > 0:
            self.executeChild(output_index=2)
        return
        #self.markDescendantsDirty()
        #self.evalChildren()
    def setSeed(self):
        self.content.seed.setText(str(self.seed))
    def onInputChanged(self, socket=None):
        pass
        #self.eval()

